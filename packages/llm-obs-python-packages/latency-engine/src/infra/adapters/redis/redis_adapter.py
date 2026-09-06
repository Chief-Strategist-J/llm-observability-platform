"""
Algorithm Summary: Infrastructure Redis Adapter.
Provides direct Redis client access for key scanning, raw GET queries, SLO violation aggregations,
and baseline percentile cache storage. Uses @traced_adapter to capture trace_id context and eliminate
repetitive inline tracing blocks. Leverages Redis pipelining and functional transform pipelines without explicit loops or conditionals.
"""
from __future__ import annotations
from typing import Any
import redis
from shared.ports.redis_port import RedisPort
from shared.tracing.tracer import traced_adapter

def _parse_int_safe(val: Any) -> int:
    try:
        return int(val) if val is not None else 0
    except (ValueError, TypeError):
        return 0

class RedisAdapter(RedisPort):
    def __init__(self, url: str):
        self.client = redis.Redis.from_url(url)

    @traced_adapter("redis")
    def scan_keys(self, pattern: str) -> list[str]:
        keys = self.client.keys(pattern)
        return list(map(lambda k: k.decode("utf-8") if isinstance(k, bytes) else str(k), keys))

    @traced_adapter("redis")
    def get_key(self, key: str) -> str | None:
        val = self.client.get(key)
        return None if val is None else (val.decode("utf-8") if isinstance(val, bytes) else str(val))

    @traced_adapter("redis")
    def get_slo_violation_count(self, model: str, endpoint: str, hour_timestamp: int) -> int:
        start_bucket = hour_timestamp // 60
        pipe = self.client.pipeline()
        list(map(lambda offset: pipe.get(f"slo:errors:{model}:{endpoint}:{start_bucket + offset}"), range(60)))
        results = pipe.execute()
        return sum(map(_parse_int_safe, results))

    @traced_adapter("redis")
    def set_baseline_p99_ttft(self, model: str, endpoint: str, hour_of_day: int, value: float) -> None:
        key = f"baseline:p99_ttft:{model}:{endpoint}:{hour_of_day}"
        self.client.set(key, str(value))
