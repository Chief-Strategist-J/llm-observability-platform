from __future__ import annotations

import numpy as np


class MiniLMScorerAdapter:
    _name: str = "minilm"
    _model_id: str = "sentence-transformers/all-MiniLM-L6-v2"

    @property
    def name(self) -> str:
        return self._name

    @property
    def model_id(self) -> str:
        return self._model_id

    def compute(
        self,
        prompt_embedding: list[float],
        response_embedding: list[float],
    ) -> float:
        a = np.array(prompt_embedding, dtype=np.float32)
        b = np.array(response_embedding, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
