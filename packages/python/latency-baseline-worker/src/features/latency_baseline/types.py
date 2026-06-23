from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class LatencyCheckpointResult:
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
