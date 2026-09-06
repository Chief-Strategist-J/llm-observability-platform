"""
Algorithm Summary: Latency Redis Analytics Read Adapter.
Provides read-only query access for DDSketch logarithmic structures, multi-window SLO request counters,
and request duration attributions from Redis storage. Uses @traced_adapter to capture trace_id context and
record execution metrics without inline tracing code blocks. Operates using pipelining and functional mapping pipelines.
"""
from __future__ import annotations
import base64
import logging
import time
from typing import Any
import redis
from ddsketch import DDSketch
from ddsketch.pb import ddsketch_pb2
from ddsketch.pb.proto import DDSketchProto

from shared.tracing.tracer import traced_adapter

logger = logging.getLogger(__name__)

_MAX_SLO_WINDOW_MINUTES = 360

def _raise_err(exc: Exception) -> None:
    raise exc

def _parse_int_safe(val: Any) -> int:
    try:
        return int(val) if val is not None else 0
    except (ValueError, TypeError):
        return 0

def _parse_float_safe(val: Any) -> float:
    try:
        return float(val) if val is not None else 0.0
    except (ValueError, TypeError):
        return 0.0

def _deserialize_sketch(b64_str: str) -> DDSketch | None:
    try:
        binary_data = base64.b64decode(b64_str)
        proto_msg = ddsketch_pb2.DDSketch()
        proto_msg.ParseFromString(binary_data)
        return DDSketchProto.from_proto(proto_msg)
    except Exception as exc:
        logger.warning("Skipping sketch payload due to error: %s", exc)
        return None

def _serialize_sketch(sketch: DDSketch) -> str:
    proto_msg = DDSketchProto.to_proto(sketch)
    return base64.b64encode(proto_msg.SerializeToString()).decode("utf-8")

def _merge_sketches(acc: DDSketch | None, s: DDSketch | None) -> DDSketch | None:
    if acc is None:
        return s
    if s is not None:
        acc.merge(s)
    return acc

class LatencyRedisAdapter:
    def __init__(self, redis_client: redis.Redis) -> None:
        self._redis = redis_client

    @traced_adapter("redis")
    def get_sketch_b64(self, model: str, hour_of_day: int) -> str | None:
        pattern = f"sketch:total:{model}:*:{hour_of_day}"
        raw_keys = self._redis.keys(pattern)
        keys = list(map(lambda k: k.decode("utf-8") if isinstance(k, bytes) else str(k), raw_keys))

        if not keys:
            return None

        raw_values = map(lambda key: self._redis.get(key), keys)
        valid_b64s = filter(lambda raw: raw is not None, raw_values)
        decoded_b64s = map(lambda raw: raw.decode("utf-8") if isinstance(raw, bytes) else str(raw), valid_b64s)
        sketches = filter(lambda s: s is not None, map(_deserialize_sketch, decoded_b64s))

        merged: DDSketch | None = None
        for s in sketches:
            merged = _merge_sketches(merged, s)

        return None if merged is None else _serialize_sketch(merged)

    @traced_adapter("redis")
    def get_slo_counts(
        self,
        model: str,
        endpoint: str,
        window_minutes: int,
    ) -> tuple[int, int]:
        not (1 <= window_minutes <= _MAX_SLO_WINDOW_MINUTES) and _raise_err(
            ValueError(f"window_minutes must be between 1 and {_MAX_SLO_WINDOW_MINUTES}")
        )

        now_bucket = int(time.time()) // 60
        pipe = self._redis.pipeline(transaction=False)

        list(map(
            lambda offset: (
                pipe.get(f"slo:total:{model}:{endpoint}:{now_bucket - offset}"),
                pipe.get(f"slo:errors:{model}:{endpoint}:{now_bucket - offset}")
            ),
            range(window_minutes)
        ))

        results = pipe.execute()
        total_requests = sum(map(_parse_int_safe, results[0::2]))
        total_errors = sum(map(_parse_int_safe, results[1::2]))

        return total_requests, total_errors

    @traced_adapter("redis")
    def get_attribution_avg(self, model: str, hour: str) -> dict[str, float] | None:
        key = f"attr:avg:{model}:{hour}"
        if not self._redis.exists(key):
            return None

        raw_hash = self._redis.hgetall(key)
        if not raw_hash:
            return None

        fields = ["dns", "tcp", "queue", "inference"]
        parsed = map(
            lambda f: (
                f,
                _parse_float_safe(
                    raw_hash.get(f.encode("utf-8")) or raw_hash.get(f)
                )
            ),
            fields
        )

        return dict(parsed)
