from __future__ import annotations
from typing import Protocol


class LatencyRedisPort(Protocol):
    """Read-only Redis port for latency query operations."""

    def get_sketch_b64(self, model: str, hour_of_day: int) -> str | None:
        """
        Reads and merges all sketch:total:{model}:*:{hour_of_day} keys.
        Returns base64-encoded merged DDSketch, or None if no keys exist.
        """
        ...

    def get_slo_counts(
        self,
        model: str,
        endpoint: str,
        window_minutes: int,
    ) -> tuple[int, int]:
        """
        Returns (total_requests, total_errors) for the given model/endpoint
        over the last `window_minutes` minutes of SLO buckets.
        """
        ...

    def get_attribution_avg(self, model: str, hour: str) -> dict[str, float] | None:
        """
        Reads the attribution hash for the given model and hour string from Redis.
        Returns a dictionary of float segment averages, or None if the key does not exist.
        """
        ...

