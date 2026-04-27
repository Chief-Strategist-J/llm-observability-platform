from __future__ import annotations

import hashlib
from typing import Dict, Tuple

from sentence_transformers import SentenceTransformer


class TemplateEmbeddingCache:
    def __init__(self, dim: int = 384, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.dim = dim
        self.model_name = model_name
        self._cache: Dict[str, Tuple[float, ...]] = {}
        self._model = None

    def get_or_compute(self, template_id: str, template_text: str) -> Tuple[float, ...]:
        if template_id in self._cache:
            return self._cache[template_id]

        vector = self._compute_with_model(template_text)
        if vector is None:
            vector = self._compute_deterministic(template_text)
        self._cache[template_id] = vector
        return vector

    def _compute_with_model(self, template_text: str) -> Tuple[float, ...] | None:
        try:
            model = self._get_model()
            embedding = model.encode([template_text], normalize_embeddings=True)[0]
            data = tuple(float(v) for v in embedding[: self.dim])
            if len(data) < self.dim:
                data = data + (0.0,) * (self.dim - len(data))
            return data
        except Exception:
            return None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _compute_deterministic(self, template_text: str) -> Tuple[float, ...]:
        digest = hashlib.sha256(template_text.encode("utf-8")).digest()
        values = []
        for i in range(self.dim):
            byte = digest[i % len(digest)]
            values.append((byte / 127.5) - 1.0)
        return tuple(values)
