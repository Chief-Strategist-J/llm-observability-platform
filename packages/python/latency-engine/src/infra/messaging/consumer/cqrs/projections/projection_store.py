from __future__ import annotations

import threading
from typing import Any


class ProjectionStore:
    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self._lock = threading.Lock()

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._store.get(key, default)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
