from __future__ import annotations
from typing import Protocol, Any


class RedisPort(Protocol):
    """Port for Redis operations in quality baseline and engine."""

    def set_baseline_quality(
        self, model: str, endpoint: str, prompt_type: str, score: float
    ) -> None: ...

    def get_baseline_quality(
        self, model: str, endpoint: str, prompt_type: str
    ) -> float | None: ...
