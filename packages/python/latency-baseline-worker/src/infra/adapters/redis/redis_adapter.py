from typing import List
import redis
from shared.ports.redis_port import RedisPort
from shared.tracing.tracer import trace_span

class RedisAdapter(RedisPort):
    def __init__(self, url: str):
        self.client = redis.Redis.from_url(url)

    def scan_keys(self, pattern: str) -> list[str]:
        with trace_span(
            "redis:scan_keys",
            attributes={
                "db.system": "redis",
                "pattern": pattern
            }
        ):
            # Convert bytes to string
            keys = self.client.keys(pattern)
            return [k.decode("utf-8") if isinstance(k, bytes) else str(k) for k in keys]

    def get_key(self, key: str) -> str | None:
        with trace_span(
            "redis:get_key",
            attributes={
                "db.system": "redis",
                "key": key
            }
        ):
            val = self.client.get(key)
            if val is None:
                return None
            return val.decode("utf-8") if isinstance(val, bytes) else str(val)

    def get_slo_violation_count(self, model: str, endpoint: str, hour_timestamp: int) -> int:
        with trace_span(
            "redis:get_slo_violation_count",
            attributes={
                "db.system": "redis",
                "model": model,
                "endpoint": endpoint,
                "hour_timestamp": hour_timestamp
            }
        ):
            start_bucket = hour_timestamp // 60
            pipe = self.client.pipeline()
            for offset in range(60):
                bucket = start_bucket + offset
                key = f"slo:errors:{model}:{endpoint}:{bucket}"
                pipe.get(key)
            
            results = pipe.execute()
            total_errors = 0
            for r in results:
                if r is not None:
                    try:
                        total_errors += int(r)
                    except ValueError:
                        pass
            return total_errors

    def set_baseline_p99_ttft(self, model: str, endpoint: str, hour_of_day: int, value: float) -> None:
        with trace_span(
            "redis:set_baseline_p99_ttft",
            attributes={
                "db.system": "redis",
                "model": model,
                "endpoint": endpoint,
                "hour_of_day": hour_of_day,
                "value": value
            }
        ):
            # Redis baseline comparison key
            # Let's save under a deterministic key pattern
            key = f"baseline:p99_ttft:{model}:{endpoint}:{hour_of_day}"
            self.client.set(key, str(value))
