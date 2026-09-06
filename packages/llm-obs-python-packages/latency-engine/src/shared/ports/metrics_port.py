from __future__ import annotations
from typing import Protocol


class MetricsPort(Protocol):
    """Port for recording Prometheus metrics in latency-engine."""

    def record_span_processed(self, model: str, endpoint: str, retry_count: int) -> None:
        """Records a processed span metric."""
        ...

    def record_sketch_dropped(self, key: str, count: int) -> None:
        """Records a metric indicating how many sketch updates were dropped."""
        ...
