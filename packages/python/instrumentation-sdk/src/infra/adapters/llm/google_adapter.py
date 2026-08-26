from typing import Any, Dict, Optional
from src.features.spans.types import FinishReason
from .port import LlmProviderAdapterPort

class GoogleGeminiAdapter(LlmProviderAdapterPort):
    def provider_name(self) -> str:
        return "google"

    def map_response(self, response: Any, model: Optional[str] = None) -> Dict[str, Any]:
        usage = getattr(response, "usage_metadata", None)
        candidates = getattr(response, "candidates", [])
        
        finish_reason = FinishReason.UNSPECIFIED
        if candidates and hasattr(candidates[0], "finish_reason"):
            reason = str(candidates[0].finish_reason).lower()
            if "stop" in reason:
                finish_reason = FinishReason.STOP
            elif "max_tokens" in reason or "length" in reason:
                finish_reason = FinishReason.LENGTH
            elif "safety" in reason or "block" in reason:
                finish_reason = FinishReason.CONTENT_FILTER

        prompt_tokens = getattr(usage, "prompt_token_count", 1) if usage else 1
        completion_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0
        text = getattr(response, "text", "")

        return {
            "model": model or getattr(response, "model_version", "gemini-1.5-pro"),
            "provider": self.provider_name(),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "finish_reason": finish_reason,
            "response_content": text,
        }
