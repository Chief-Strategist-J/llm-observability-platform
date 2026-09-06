from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PercentilesResponseDTO:
    p50: float
    p95: float
    p99: float
    sample_count: int


@dataclass(frozen=True)
class SLOResponseDTO:
    burn_fast: float
    burn_medium: float
    burn_slow: float
    budget_remaining_pct: float
    slo_threshold_ms: float


@dataclass(frozen=True)
class BaselinePointDTO:
    date: date
    p99_ttft_ms: float
    p99_total_ms: float


@dataclass(frozen=True)
class AttributionResponseDTO:
    dns: float
    tcp: float
    queue: float
    inference: float
