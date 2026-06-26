from __future__ import annotations

import base64
import logging
import time

import redis
from ddsketch import DDSketch
from ddsketch.pb import ddsketch_pb2
from ddsketch.pb.proto import DDSketchProto

from shared.tracing.tracer import api_span

logger = logging.getLogger(__name__)

# SLO keys older than 6 hours are expired by the writer — 360 minute max window
_MAX_SLO_WINDOW_MINUTES = 360


class LatencyRedisAdapter:
    """
    Read-only Redis adapter for latency query operations.
    Implements LatencyRedisPort structurally (Protocol).

    All IO is wrapped in child OTEL spans.
    All vendor errors are caught and re-raised with context.
    No business logic — only translation between Redis primitives and port types.
    """

    def __init__(self, redis_client: redis.Redis) -> None:
        self._redis = redis_client

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _deserialize_sketch(self, b64_str: str) -> DDSketch:
        binary_data = base64.b64decode(b64_str)
        proto_msg = ddsketch_pb2.DDSketch()
        proto_msg.ParseFromString(binary_data)
        return DDSketchProto.from_proto(proto_msg)

    def _serialize_sketch(self, sketch: DDSketch) -> str:
        proto_msg = DDSketchProto.to_proto(sketch)
        return base64.b64encode(proto_msg.SerializeToString()).decode("utf-8")

    # ------------------------------------------------------------------
    # Port implementation
    # ------------------------------------------------------------------

    def get_sketch_b64(self, model: str, hour_of_day: int) -> str | None:
        """
        Scans all sketch:total:{model}:*:{hour_of_day} keys, merges them
        into a single DDSketch and returns its base64 serialization.
        Returns None if no matching keys exist.
        """
        with api_span(
            "redis_adapter.get_sketch_b64",
            {"db.system": "redis", "model": model, "hour_of_day": hour_of_day},
        ):
            pattern = f"sketch:total:{model}:*:{hour_of_day}"
            try:
                raw_keys = self._redis.keys(pattern)
            except redis.RedisError as exc:
                logger.error("Redis KEYS failed for pattern %s: %s", pattern, exc)
                raise

            keys = [
                k.decode("utf-8") if isinstance(k, bytes) else str(k)
                for k in raw_keys
            ]
            if not keys:
                return None

            merged: DDSketch | None = None
            for key in keys:
                try:
                    raw = self._redis.get(key)
                    if raw is None:
                        continue
                    b64 = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
                    sketch = self._deserialize_sketch(b64)
                    if merged is None:
                        merged = sketch
                    else:
                        merged.merge(sketch)
                except Exception as exc:
                    logger.warning("Skipping sketch key %s due to error: %s", key, exc)

            if merged is None:
                return None
            return self._serialize_sketch(merged)

    def get_slo_counts(
        self,
        model: str,
        endpoint: str,
        window_minutes: int,
    ) -> tuple[int, int]:
        """
        Returns (total_requests, total_errors) by summing slo:total and
        slo:errors buckets over the last `window_minutes` 1-minute buckets.
        Uses a Redis pipeline for efficiency.
        """
        if window_minutes < 1 or window_minutes > _MAX_SLO_WINDOW_MINUTES:
            raise ValueError(
                f"window_minutes must be between 1 and {_MAX_SLO_WINDOW_MINUTES}"
            )

        with api_span(
            "redis_adapter.get_slo_counts",
            {
                "db.system": "redis",
                "model": model,
                "endpoint": endpoint,
                "window_minutes": window_minutes,
            },
        ):
            now_bucket = int(time.time()) // 60
            pipe = self._redis.pipeline(transaction=False)

            for offset in range(window_minutes):
                bucket = now_bucket - offset
                pipe.get(f"slo:total:{model}:{endpoint}:{bucket}")
                pipe.get(f"slo:errors:{model}:{endpoint}:{bucket}")

            try:
                results = pipe.execute()
            except redis.RedisError as exc:
                logger.error("Redis pipeline failed for SLO counts: %s", exc)
                raise

            total_requests = 0
            total_errors = 0
            for i in range(0, len(results), 2):
                raw_total = results[i]
                raw_errors = results[i + 1]
                if raw_total is not None:
                    try:
                        total_requests += int(raw_total)
                    except (ValueError, TypeError):
                        pass
                if raw_errors is not None:
                    try:
                        total_errors += int(raw_errors)
                    except (ValueError, TypeError):
                        pass

            return total_requests, total_errors
