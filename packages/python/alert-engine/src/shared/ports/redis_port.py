from typing import Protocol

class RedisPort(Protocol):
    def acquire_rate_limit(self, key: str, ttl_seconds: int) -> bool: ...
