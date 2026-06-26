from __future__ import annotations

import base64
import logging

from ddsketch import DDSketch
from ddsketch.pb import ddsketch_pb2
from ddsketch.pb.proto import DDSketchProto

from shared.ports.latency_redis_port import LatencyRedisPort
from shared.ports.latency_clickhouse_port import LatencyClickHousePort
from shared.errors.latency_query_errors import (
    BaselineNotFoundError,
    InvalidQuantileError,
    SketchNotFoundError,
    SLODataNotFoundError,
)
from features.latency_query.types import BaselinePoint, PercentilesResult, SLOResult

logger = logging.getLogger(__name__)

# SLO budget target: 99.9% availability over a 30-day window
_SLO_TARGET = 0.999
_ERROR_BUDGET_PCT = (1.0 - _SLO_TARGET) * 100.0  # 0.1%
# Minutes per window
_WINDOW_FAST_MIN = 60
_WINDOW_MEDIUM_MIN = 360
_WINDOW_SLOW_MIN = 4320  # 3 days


def _deserialize_sketch(b64_str: str) -> DDSketch:
    binary_data = base64.b64decode(b64_str)
    proto_msg = ddsketch_pb2.DDSketch()
    proto_msg.ParseFromString(binary_data)
    return DDSketchProto.from_proto(proto_msg)


def _compute_burn_rate(total: int, errors: int) -> float:
    """
    Burn rate = (error_rate / (1 - SLO_target)).
    Returns 0.0 when total == 0 to avoid division-by-zero.
    """
    if total == 0:
        return 0.0
    error_rate = errors / total
    allowed_error_rate = 1.0 - _SLO_TARGET
    return error_rate / allowed_error_rate


class LatencyQueryService:
    """
    Pure business logic for latency query operations.
    Zero IO — all data access through injected port interfaces.
    No HTTP, no framework imports.
    """

    def __init__(
        self,
        redis: LatencyRedisPort,
        clickhouse: LatencyClickHousePort,
        slo_thresholds: dict[str, float],
    ) -> None:
        self._redis = redis
        self._clickhouse = clickhouse
        self._slo_thresholds = slo_thresholds

    # ------------------------------------------------------------------
    # Use-case: percentiles
    # ------------------------------------------------------------------

    def get_percentiles(
        self,
        model: str,
        hour_of_day: int,
        quantiles: list[float],
    ) -> PercentilesResult:
        """
        Reads the merged DDSketch for model+hour and returns the requested
        quantile values. Quantiles must contain exactly 0.50, 0.95, 0.99
        (additional values are ignored after extraction).

        Raises:
            InvalidQuantileError: if any quantile is not in (0, 1)
            SketchNotFoundError: if no sketch exists for model+hour
        """
        for q in quantiles:
            if not (0.0 < q < 1.0):
                raise InvalidQuantileError(
                    f"Quantile {q} is out of range; must be in (0, 1)"
                )

        b64 = self._redis.get_sketch_b64(model, hour_of_day)
        if b64 is None:
            raise SketchNotFoundError(
                f"No sketch found for model={model!r} hour_of_day={hour_of_day}"
            )

        try:
            sketch = _deserialize_sketch(b64)
        except Exception as exc:
            raise SketchNotFoundError(
                f"Failed to deserialize sketch for model={model!r}: {exc}"
            ) from exc

        # Extract the three standard quantiles; default to 0.0 if quantile not requested
        q_map = {q: sketch.get_quantile_value(q) for q in quantiles}
        p50 = q_map.get(0.50, sketch.get_quantile_value(0.50))
        p95 = q_map.get(0.95, sketch.get_quantile_value(0.95))
        p99 = q_map.get(0.99, sketch.get_quantile_value(0.99))

        # DDSketch returns None for empty sketches (count == 0)
        if any(v is None for v in (p50, p95, p99)):
            raise SketchNotFoundError(
                f"Sketch for model={model!r} hour={hour_of_day} is empty (count=0)"
            )

        return PercentilesResult(
            p50=round(float(p50), 1),
            p95=round(float(p95), 1),
            p99=round(float(p99), 1),
            sample_count=int(sketch.count),
        )

    # ------------------------------------------------------------------
    # Use-case: SLO burn rates
    # ------------------------------------------------------------------

    def get_slo(self, model: str, endpoint: str) -> SLOResult:
        """
        Computes multi-window SLO burn rates and error-budget remaining.

        Windows:
          - fast   = 1 hour  (60 min buckets)
          - medium = 6 hours (360 min buckets)
          - slow   = 3 days  (4320 min buckets, capped by Redis TTL at 6 hours)

        Note: the latency-engine writer expires SLO keys after 6 hours,
        so the slow window uses 6-hour data as a best-effort 3-day proxy.

        Raises:
            SLODataNotFoundError: if no SLO data exists for model+endpoint
        """
        total_fast, errors_fast = self._redis.get_slo_counts(
            model, endpoint, _WINDOW_FAST_MIN
        )
        total_medium, errors_medium = self._redis.get_slo_counts(
            model, endpoint, _WINDOW_MEDIUM_MIN
        )
        # 3-day window capped at max 6 hours due to Redis TTL
        total_slow, errors_slow = self._redis.get_slo_counts(
            model, endpoint, _WINDOW_MEDIUM_MIN  # 6h best-effort
        )

        if total_fast == 0 and total_medium == 0:
            raise SLODataNotFoundError(
                f"No SLO data found for model={model!r} endpoint={endpoint!r}"
            )

        burn_fast = _compute_burn_rate(total_fast, errors_fast)
        burn_medium = _compute_burn_rate(total_medium, errors_medium)
        burn_slow = _compute_burn_rate(total_slow, errors_slow)

        # Budget remaining: measured over the medium window (most stable)
        if total_medium > 0:
            error_rate_medium = errors_medium / total_medium
            consumed_budget = (error_rate_medium / (1.0 - _SLO_TARGET)) * 100.0
            budget_remaining = max(0.0, 100.0 - consumed_budget)
        else:
            budget_remaining = 100.0

        threshold = self._slo_thresholds.get(
            endpoint, self._slo_thresholds.get("default", 500.0)
        )

        return SLOResult(
            burn_fast=round(burn_fast, 3),
            burn_medium=round(burn_medium, 3),
            burn_slow=round(burn_slow, 3),
            budget_remaining_pct=round(budget_remaining, 1),
            slo_threshold_ms=float(threshold),
        )

    # ------------------------------------------------------------------
    # Use-case: baseline history
    # ------------------------------------------------------------------

    def get_baseline(
        self,
        model: str,
        hour_of_day: int,
        days: int,
    ) -> list[BaselinePoint]:
        """
        Fetches daily p99 TTFT and p99 total latency from ClickHouse
        for the given model and hour, over the past `days` days.

        Raises:
            BaselineNotFoundError: if no rows are returned
        """
        if days < 1 or days > 90:
            raise ValueError("days must be between 1 and 90")

        rows = self._clickhouse.get_baseline(model, hour_of_day, days)
        if not rows:
            raise BaselineNotFoundError(
                f"No baseline data for model={model!r} hour={hour_of_day} days={days}"
            )

        return [
            BaselinePoint(
                date=row.checkpoint_date,
                p99_ttft_ms=round(row.p99_ttft_ms, 1),
                p99_total_ms=round(row.p99_total_ms, 1),
            )
            for row in rows
        ]
