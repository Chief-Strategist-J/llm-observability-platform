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

class ClickHouseQueryRegistry:
    BASELINE_QUERY = """
SELECT
    checkpoint_date,
    p99_ttft_ms,
    p99_total_ms
FROM latency_checkpoints
WHERE model = %(model)s
  AND hour_of_day = %(hour_of_day)s
  AND checkpoint_date >= today() - %(days)s
ORDER BY checkpoint_date DESC
LIMIT %(days)s
"""

    P99_TTFT_HISTORY_QUERY = """
SELECT p99_ttft_ms
FROM latency_checkpoints
WHERE model = %(model)s
  AND endpoint = %(endpoint)s
  AND hour_of_day = %(hour_of_day)s
  AND timestamp >= now() - INTERVAL 7 DAY
ORDER BY timestamp DESC
"""
