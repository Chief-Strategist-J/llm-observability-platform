from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PercentilesResult:
    """Output of the percentiles query. All latencies in milliseconds."""
    p50: float
    p95: float
    p99: float
    sample_count: int


@dataclass(frozen=True)
class SLOResult:
    """Output of the SLO burn rate query."""
    burn_fast: float       # 1-hour burn rate
    burn_medium: float     # 6-hour burn rate
    burn_slow: float       # 3-day (72-hour) burn rate
    budget_remaining_pct: float
    slo_threshold_ms: float


@dataclass(frozen=True)
class BaselinePoint:
    """One daily baseline checkpoint row."""
    date: date
    p99_ttft_ms: float
    p99_total_ms: float
