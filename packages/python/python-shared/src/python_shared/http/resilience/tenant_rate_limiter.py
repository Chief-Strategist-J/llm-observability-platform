import time
import threading
from typing import Dict, Tuple

class TenantRateLimiter:
    def __init__(self, capacity: float = 100.0, fill_rate_per_sec: float = 50.0):
        self.capacity = capacity
        self.fill_rate_per_sec = fill_rate_per_sec
        self._buckets: Dict[str, Tuple[float, float]] = {}
        self._lock = threading.RLock()

    def allow_request(self, tenant_id: str, tokens: float = 1.0) -> bool:
        now = time.time()
        with self._lock:
            current_tokens, last_refill = self._buckets.get(tenant_id, (self.capacity, now))
            elapsed = now - last_refill
            refilled = min(self.capacity, current_tokens + elapsed * self.fill_rate_per_sec)

            if refilled >= tokens:
                self._buckets[tenant_id] = (refilled - tokens, now)
                return True
            self._buckets[tenant_id] = (refilled, now)
            return False

    def allow(self, key: str, tokens: float = 1.0) -> bool:
        return self.allow_request(key, tokens)

TokenBucketLimiter = TenantRateLimiter
