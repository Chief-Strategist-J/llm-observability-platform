from __future__ import annotations
from dataclasses import dataclass, fields
from datetime import date, datetime

@dataclass
class LatencyCheckpointModel:
    model: str
    endpoint: str
    checkpoint_date: date
    hour_of_day: int
    p50_ttft_ms: float
    p95_ttft_ms: float
    p99_ttft_ms: float
    p50_total_ms: float
    p95_total_ms: float
    p99_total_ms: float
    sample_count: int
    slo_violation_count: int
    timestamp: datetime

    @classmethod
    def table_name(cls) -> str:
        return "latency_checkpoints"

    @classmethod
    def column_names(cls) -> list[str]:
        return [f.name for f in fields(cls)]
