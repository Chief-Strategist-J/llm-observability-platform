from __future__ import annotations
from typing import Protocol


class BaselineCachePort(Protocol):
    """Port for reading and writing rolling quality baseline scores in Redis."""

    def get_baseline(self, model: str, endpoint: str, prompt_type: str) -> float | None: ...

    def set_baseline(
        self,
        model: str,
        endpoint: str,
        prompt_type: str,
        value: float,
        ttl_seconds: int = 691200,  # 8 days
    ) -> None: ...

    def is_alert_rate_limited(self, model: str, endpoint: str) -> bool: ...

    def set_alert_rate_limit(self, model: str, endpoint: str, ttl_seconds: int = 3600) -> None: ...
