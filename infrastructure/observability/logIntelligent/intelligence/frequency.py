from __future__ import annotations

import hashlib
import math
import threading
from typing import Iterable


class CountMinSketch:
    """
    Thread-safe Count-Min Sketch probabilistic counter.
    
    All operations are protected by an internal lock to ensure
    atomicity in multi-threaded environments (e.g., FastAPI thread pool).
    """

    def __init__(self, width: int = 2000, depth: int = 7) -> None:
        self.width = width
        self.depth = depth
        self._tables = [[0] * width for _ in range(depth)]
        self._lock = threading.Lock()

    def _indexes(self, key: str) -> Iterable[int]:
        payload = key.encode("utf-8")
        for row in range(self.depth):
            digest = hashlib.blake2b(payload, digest_size=8, person=f"cms{row}".encode("utf-8")).digest()
            yield int.from_bytes(digest, "big") % self.width

    def add(self, key: str, count: int = 1) -> None:
        """Add a count to the sketch in a thread-safe manner."""
        with self._lock:
            for row, index in enumerate(self._indexes(key)):
                self._tables[row][index] += count

    def estimate(self, key: str) -> int:
        """Estimate the count for a key (read-only operation)."""
        with self._lock:
            return min(self._tables[row][index] for row, index in enumerate(self._indexes(key)))

    @property
    def epsilon(self) -> float:
        return math.e / self.width

    @property
    def delta(self) -> float:
        return math.exp(-self.depth)
