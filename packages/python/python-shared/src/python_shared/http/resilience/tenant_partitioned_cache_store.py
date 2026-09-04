import time
import threading
from typing import Dict, Any, Optional

class CacheEntry:
    def __init__(self, value: Any, expires_at: float):
        self.value = value
        self.expires_at = expires_at

class TenantPartitionedCacheStore:
    def __init__(self, max_partition_size: int = 100):
        self.max_partition_size = max_partition_size
        self._partitions: Dict[str, Dict[str, CacheEntry]] = {}
        self._lock = threading.RLock()

    def get(self, tenant_id: str, key: str) -> Optional[Any]:
        with self._lock:
            partition = self._partitions.get(tenant_id)
            if not partition:
                return None
            entry = partition.get(key)
            if not entry:
                return None
            if time.time() >= entry.expires_at:
                del partition[key]
                return None
            return entry.value

    def set(self, tenant_id: str, key: str, value: Any, ttl_ms: float = 5000.0) -> None:
        with self._lock:
            partition = self._partitions.setdefault(tenant_id, {})
            if len(partition) >= self.max_partition_size:
                oldest_key = next(iter(partition.keys()), None)
                if oldest_key:
                    del partition[oldest_key]
            expires_at = time.time() + (ttl_ms / 1000.0)
            partition[key] = CacheEntry(value, expires_at)

    def clear(self, tenant_id: str) -> None:
        with self._lock:
            self._partitions.pop(tenant_id, None)

    def clear_all(self) -> None:
        with self._lock:
            self._partitions.clear()
