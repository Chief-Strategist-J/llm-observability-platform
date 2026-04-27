from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import numpy as np
from sklearn.neighbors import NearestNeighbors


class HNSWLikeIndex:
    def __init__(self) -> None:
        self._vectors: Dict[str, Tuple[float, ...]] = {}
        self._model = None
        self._keys: List[str] = []

    def upsert(self, template_id: str, vector: Tuple[float, ...]) -> None:
        self._vectors[template_id] = vector
        self._rebuild_index()

    def query(self, vector: Sequence[float], k: int = 5) -> List[str]:
        if not self._vectors:
            return []
        if self._model is None or not self._keys:
            self._rebuild_index()
        neighbors = min(k, len(self._keys))
        distances, indices = self._model.kneighbors(np.array([vector]), n_neighbors=neighbors)
        return [self._keys[index] for index in indices[0]]

    def _rebuild_index(self) -> None:
        self._keys = list(self._vectors.keys())
        matrix = np.array([self._vectors[key] for key in self._keys])
        self._model = NearestNeighbors(metric="cosine", algorithm="brute")
        self._model.fit(matrix)
