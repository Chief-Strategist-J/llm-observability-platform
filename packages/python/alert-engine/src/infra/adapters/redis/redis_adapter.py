import time
import redis
from opentelemetry import trace
from shared.ports.redis_port import RedisPort

tracer = trace.get_tracer("alert-engine")

class RedisAdapter(RedisPort):
    def __init__(self, redis_url: str):
        self.client = redis.from_url(redis_url)

    def acquire_rate_limit(self, key: str, ttl_seconds: int) -> bool:
        with tracer.start_as_current_span(
            "redis_adapter.acquire_rate_limit",
            attributes={
                "db.system": "redis",
                "redis.key": key,
                "redis.ttl_seconds": ttl_seconds,
            }
        ) as span:
            try:
                res = self.client.set(key, str(time.time()), nx=True, ex=ttl_seconds)
                acquired = res is not None
                span.set_attribute("redis.acquired", acquired)
                return acquired
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
                raise
