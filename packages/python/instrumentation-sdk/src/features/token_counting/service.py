import base64
import struct
import math
from typing import Union, List, Dict, Any, Tuple, Optional
from .ports import TokenEncoderPort
from ..manual_instrumentation.service import LLMSpanContext
from ..spans.index import TokenCountMethod

class LLMSpanWithTokensContext(LLMSpanContext):
    def __init__(self, service: "TokenCountingService", prompt: Any, **kwargs: Any):
        super().__init__(**kwargs)
        model = kwargs.get("model", "")
        tokens, method = service.count_tokens(prompt, model)
        self.set_metadata("prompt_tokens", tokens)
        self.set_metadata("token_count_method", method)

class TokenCountingService:
    def __init__(self, encoder: TokenEncoderPort):
        self._encoder = encoder

    def count_tokens(self, prompt: Union[str, List[Dict[str, Any]]], model: str) -> Tuple[int, str]:
        if isinstance(prompt, str):
            try:
                encoding = self._encoder.get_encoding(model)
                tokens = self._encoder.encode(encoding, prompt)
                return len(tokens), TokenCountMethod.TIKTOKEN.value
            except Exception:
                return self._estimate_text_tokens(prompt, model), TokenCountMethod.ESTIMATED.value

        if isinstance(prompt, list):
            try:
                encoding = self._encoder.get_encoding(model)
                return self._count_messages_tiktoken(encoding, prompt, model), TokenCountMethod.TIKTOKEN.value
            except Exception:
                return self._count_messages_estimated(prompt, model), TokenCountMethod.ESTIMATED.value

        return 0, TokenCountMethod.UNSPECIFIED.value

    def _estimate_text_tokens(self, text: str, model: str) -> int:
        model_lower = model.lower()
        if "claude" in model_lower or "anthropic" in model_lower:
            char_ratio = 3.5
        elif "llama" in model_lower or "meta" in model_lower:
            char_ratio = 3.3
        elif "gemini" in model_lower or "google" in model_lower:
            char_ratio = 3.8
        else:
            char_ratio = 4.0
        return max(1, int(len(text) / char_ratio))

    def _calculate_image_tokens(self, url: str, detail: str) -> int:
        if detail == "low":
            return 85
        width, height = self._get_image_dimensions(url)
        if detail == "auto":
            if width is not None and height is not None:
                if width <= 512 and height <= 512:
                    return 85
        if width is None or height is None:
            return 765
        w, h = width, height
        if w > 2048 or h > 2048:
            ratio = 2048 / max(w, h)
            w = int(w * ratio)
            h = int(h * ratio)
        if w < h:
            ratio = 768 / w
            w = 768
            h = int(h * ratio)
        else:
            ratio = 768 / h
            h = 768
            w = int(w * ratio)
        tiles_w = math.ceil(w / 512)
        tiles_h = math.ceil(h / 512)
        return 85 + 170 * (tiles_w * tiles_h)

    def _get_image_dimensions(self, image_url: str) -> Tuple[Optional[int], Optional[int]]:
        if not image_url.startswith("data:"):
            return None, None
        try:
            _, base64_data = image_url.split(",", 1)
            image_bytes = base64.b64decode(base64_data)
            if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
                width, height = struct.unpack(">II", image_bytes[16:24])
                return width, height
            elif image_bytes.startswith(b"GIF87a") or image_bytes.startswith(b"GIF89a"):
                width, height = struct.unpack("<HH", image_bytes[6:10])
                return width, height
            elif image_bytes.startswith(b"\xff\xd8"):
                size = len(image_bytes)
                idx = 2
                while idx < size:
                    if image_bytes[idx] == 0xFF:
                        marker = image_bytes[idx+1]
                        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                            height, width = struct.unpack(">HH", image_bytes[idx+5:idx+9])
                            return width, height
                        else:
                            length = struct.unpack(">H", image_bytes[idx+2:idx+4])[0]
                            idx += 2 + length
                    else:
                        idx += 1
        except Exception:
            pass
        return None, None

    def _count_messages_tiktoken(self, encoding: Any, messages: List[Dict[str, Any]], model: str) -> int:
        tokens_per_message = 3
        tokens_per_name = 1
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                if key == "content":
                    if isinstance(value, str):
                        num_tokens += len(self._encoder.encode(encoding, value))
                    elif isinstance(value, list):
                        for part in value:
                            if not isinstance(part, dict):
                                continue
                            part_type = part.get("type")
                            if part_type == "text":
                                num_tokens += len(self._encoder.encode(encoding, part.get("text", "")))
                            elif part_type == "image_url":
                                img_info = part.get("image_url", {})
                                if isinstance(img_info, dict):
                                    num_tokens += self._calculate_image_tokens(
                                        img_info.get("url", ""),
                                        img_info.get("detail", "auto")
                                    )
                else:
                    if isinstance(value, str):
                        num_tokens += len(self._encoder.encode(encoding, value))
                    if key == "name":
                        num_tokens += tokens_per_name
        num_tokens += 3
        return num_tokens

    def _count_messages_estimated(self, messages: List[Dict[str, Any]], model: str) -> int:
        tokens_per_message = 3
        tokens_per_name = 1
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                if key == "content":
                    if isinstance(value, str):
                        num_tokens += self._estimate_text_tokens(value, model)
                    elif isinstance(value, list):
                        for part in value:
                            if not isinstance(part, dict):
                                continue
                            part_type = part.get("type")
                            if part_type == "text":
                                num_tokens += self._estimate_text_tokens(part.get("text", ""), model)
                            elif part_type == "image_url":
                                img_info = part.get("image_url", {})
                                if isinstance(img_info, dict):
                                    num_tokens += self._calculate_image_tokens(
                                        img_info.get("url", ""),
                                        img_info.get("detail", "auto")
                                    )
                else:
                    if isinstance(value, str):
                        num_tokens += self._estimate_text_tokens(value, model)
                    if key == "name":
                        num_tokens += tokens_per_name
        num_tokens += 3
        return num_tokens

    def llm_span_with_tokens(self, model: str, provider: str, prompt: Union[str, List[Dict[str, Any]]], **kwargs: Any) -> LLMSpanWithTokensContext:
        return LLMSpanWithTokensContext(self, prompt, model=model, provider=provider, **kwargs)
