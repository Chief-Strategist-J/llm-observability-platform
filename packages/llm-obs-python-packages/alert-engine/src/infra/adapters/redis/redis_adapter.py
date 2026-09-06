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

    def get_open_incident(self, model: str, endpoint: str) -> str | None:
        with tracer.start_as_current_span(
            "redis_adapter.get_open_incident",
            attributes={"db.system": "redis", "model": model, "endpoint": endpoint}
        ) as span:
            try:
                key = f"incident:pd:{model}:{endpoint}"
                val = self.client.get(key)
                if val is None:
                    return None
                return val.decode("utf-8") if isinstance(val, bytes) else str(val)
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
                raise

    def set_open_incident(self, model: str, endpoint: str, incident_id: str, ttl: int) -> None:
        with tracer.start_as_current_span(
            "redis_adapter.set_open_incident",
            attributes={"db.system": "redis", "model": model, "endpoint": endpoint, "incident_id": incident_id}
        ) as span:
            try:
                key = f"incident:pd:{model}:{endpoint}"
                self.client.setex(key, ttl, incident_id)
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
                raise

    def delete_open_incident(self, model: str, endpoint: str) -> None:
        with tracer.start_as_current_span(
            "redis_adapter.delete_open_incident",
            attributes={"db.system": "redis", "model": model, "endpoint": endpoint}
        ) as span:
            try:
                key = f"incident:pd:{model}:{endpoint}"
                self.client.delete(key)
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
                raise

