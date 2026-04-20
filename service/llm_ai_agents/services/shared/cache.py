import threading
from typing import Any, Dict, Optional


class _InstanceCache:
    def __init__(self):
        self._lock = threading.Lock()
        self._store: Dict[str, Any] = {}

    def get(self, key: str) -> Optional[Any]:
        return self._store.get(key)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._store[key] = value

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


instance_cache = _InstanceCache()
