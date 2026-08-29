"""
Algorithm Summary: Pure Business Logic Engine for Latency Analytics Queries.
Executes multi-quantile distribution extraction from compressed logarithmic DDSketch payloads, computes multi-window
SLO burn rates (fast/medium/slow windows against 99.9% target budget), formats ClickHouse historical daily baseline
percentiles, and computes request latency attribution component breakdowns (DNS, TCP, queue, inference). Driven by functional
map-filter transformation pipelines and rule evaluation without imperative conditional branching or loop constructs.
"""
from __future__ import annotations
import base64
import logging
from typing import Any
from ddsketch import DDSketch
from ddsketch.pb import ddsketch_pb2
from ddsketch.pb.proto import DDSketchProto

from features.latency_query.repository import LatencyQueryRepository
from shared.errors.latency_query_errors import (
    BaselineNotFoundError,
    InvalidQuantileError,
    SketchNotFoundError,
    SLODataNotFoundError,
    AttributionNotFoundError,
)
from features.latency_query.types import BaselinePoint, PercentilesResult, SLOResult, AttributionResult

logger = logging.getLogger(__name__)

_SLO_TARGET = 0.999
_WINDOW_FAST_MIN = 60
_WINDOW_MEDIUM_MIN = 360

def _raise_err(exc: Exception) -> None:
    raise exc

def _deserialize_sketch(b64_str: str) -> DDSketch:
    try:
        binary_data = base64.b64decode(b64_str)
        proto_msg = ddsketch_pb2.DDSketch()
        proto_msg.ParseFromString(binary_data)
        return DDSketchProto.from_proto(proto_msg)
    except Exception as exc:
        raise SketchNotFoundError(f"Failed to deserialize sketch: {exc}") from exc

def _compute_burn_rate(total: int, errors: int) -> float:
    return 0.0 if total == 0 else (errors / total) / (1.0 - _SLO_TARGET)

class LatencyQueryService:
    def __init__(
        self,
        repository: LatencyQueryRepository,
        slo_thresholds: dict[str, float],
    ) -> None:
        self._repository = repository
        self._slo_thresholds = slo_thresholds

    def get_percentiles(
        self,
        model: str,
        hour_of_day: int,
        quantiles: list[float],
    ) -> PercentilesResult:
        invalid_q = list(filter(lambda q: not (0.0 < q < 1.0), quantiles))
        invalid_q and _raise_err(InvalidQuantileError(f"Quantile {invalid_q[0]} is out of range; must be in (0, 1)"))

        b64 = self._repository.get_sketch_b64(model, hour_of_day)
        b64 or _raise_err(SketchNotFoundError(f"No sketch found for model={model!r} hour_of_day={hour_of_day}"))

        sketch = _deserialize_sketch(b64)
        p50, p95, p99 = map(sketch.get_quantile_value, [0.50, 0.95, 0.99])

        any(v is None for v in (p50, p95, p99)) and _raise_err(
            SketchNotFoundError(f"Sketch for model={model!r} hour={hour_of_day} is empty (count=0)")
        )

        return PercentilesResult(
            p50=round(float(p50), 1),
            p95=round(float(p95), 1),
            p99=round(float(p99), 1),
            sample_count=int(sketch.count),
        )

    def get_slo(self, model: str, endpoint: str) -> SLOResult:
        total_fast, errors_fast = self._repository.get_slo_counts(model, endpoint, _WINDOW_FAST_MIN)
        total_medium, errors_medium = self._repository.get_slo_counts(model, endpoint, _WINDOW_MEDIUM_MIN)
        total_slow, errors_slow = self._repository.get_slo_counts(model, endpoint, _WINDOW_MEDIUM_MIN)

        (total_fast == 0 and total_medium == 0) and _raise_err(
            SLODataNotFoundError(f"No SLO data found for model={model!r} endpoint={endpoint!r}")
        )

        burn_fast = _compute_burn_rate(total_fast, errors_fast)
        burn_medium = _compute_burn_rate(total_medium, errors_medium)
        burn_slow = _compute_burn_rate(total_slow, errors_slow)

        budget_remaining = 100.0 if total_medium == 0 else max(
            0.0, 100.0 - ((errors_medium / total_medium) / (1.0 - _SLO_TARGET)) * 100.0
        )
        threshold = float(self._slo_thresholds.get(endpoint, self._slo_thresholds.get("default", 500.0)))

        return SLOResult(
            burn_fast=round(burn_fast, 3),
            burn_medium=round(burn_medium, 3),
            burn_slow=round(burn_slow, 3),
            budget_remaining_pct=round(budget_remaining, 1),
            slo_threshold_ms=threshold,
        )

    def get_baseline(
        self,
        model: str,
        hour_of_day: int,
        days: int,
    ) -> list[BaselinePoint]:
        not (1 <= days <= 90) and _raise_err(ValueError("days must be between 1 and 90"))

        rows = self._repository.get_baseline(model, hour_of_day, days)
        rows or _raise_err(BaselineNotFoundError(f"No baseline data for model={model!r} hour={hour_of_day} days={days}"))

        return list(map(lambda r: BaselinePoint(
            date=r.checkpoint_date,
            p99_ttft_ms=round(r.p99_ttft_ms, 1),
            p99_total_ms=round(r.p99_total_ms, 1),
        ), rows))

    def get_attribution(
        self,
        model: str,
        hour: str,
    ) -> AttributionResult:
        data = self._repository.get_attribution(model, hour)
        data or _raise_err(AttributionNotFoundError(f"No attribution data found for model={model!r} hour={hour}"))

        return AttributionResult(
            dns=round(data.get("dns", 0.0), 1),
            tcp=round(data.get("tcp", 0.0), 1),
            queue=round(data.get("queue", 0.0), 1),
            inference=round(data.get("inference", 0.0), 1),
        )
