from __future__ import annotations
from typing import Protocol
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class BaselineRow:
    checkpoint_date: date
    p99_ttft_ms: float
    p99_total_ms: float


class LatencyClickHousePort(Protocol):
    """Read-only ClickHouse port for latency baseline query operations."""

    def get_baseline(
        self,
        model: str,
        hour_of_day: int,
        days: int,
    ) -> list[BaselineRow]:
        """
        Queries latency_checkpoints for the given model and hour_of_day,
        returning up to `days` most-recent rows ordered by date DESC.
        Each row contains checkpoint_date, p99_ttft_ms, and p99_total_ms.
        """
        ...
