from __future__ import annotations

import math
from functools import cached_property


class Gpt2OnnxAdapter:
    def __init__(self, model_path: str = "gpt2") -> None:
        self._model_path = model_path
        self._available: bool | None = None

    def is_available(self) -> bool:
        if self._available is None:
            try:
                import onnxruntime  # noqa: F401
                from transformers import GPT2TokenizerFast  # noqa: F401
                self._available = True
            except ImportError:
                self._available = False
        return self._available

    @cached_property
    def _tokenizer(self):
        from transformers import GPT2TokenizerFast
        tok = GPT2TokenizerFast.from_pretrained(self._model_path)
        tok.pad_token = tok.eos_token
        return tok

    @cached_property
    def _session(self):
        import onnxruntime as ort
        from transformers import GPT2Config
        import numpy as np
        from optimum.onnxruntime import ORTModelForCausalLM
        return ORTModelForCausalLM.from_pretrained(self._model_path, export=True)

    def compute(self, response_text: str) -> float | None:
        if not self.is_available():
            return None
        try:
            return self._compute_perplexity(response_text)
        except Exception:
            return None

    def _compute_perplexity(self, text: str) -> float:
        import torch

        enc = self._tokenizer(text, return_tensors="pt", truncation=True, max_length=1024)
        input_ids = enc["input_ids"]

        with torch.no_grad():
            outputs = self._session(input_ids=input_ids, labels=input_ids)

        loss = outputs.loss
        return math.exp(loss.item())
