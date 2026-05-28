import redis
from typing import Optional
from opentelemetry import trace
from budget_provisioner.shared.ports.redis_port import RedisPort

tracer = trace.get_tracer("budget-provisioner")

class RedisAdapter(RedisPort):
    def __init__(self, redis_url: str) -> None:
        self.client = redis.from_url(redis_url)

    def invalidate_budget_cache(self, user_id: str, model: str) -> None:
        key = f"budget:{user_id}:{model}"
        with tracer.start_as_current_span(
            "redis_adapter.invalidate_budget_cache",
            attributes={
                "db.system": "redis",
                "redis.key": key,
                "redis.operation": "delete"
            }
        ) as span:
            try:
                self.client.delete(key)
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
                raise

    def get_token_bucket_status(self, user_id: str, model: str) -> Optional[dict]:
        key = f"budget:{user_id}:{model}"
        with tracer.start_as_current_span(
            "redis_adapter.get_token_bucket_status",
            attributes={
                "db.system": "redis",
                "redis.key": key,
                "redis.operation": "get"
            }
        ) as span:
            try:
                key_type = self.client.type(key)
                if isinstance(key_type, bytes):
                    key_type = key_type.decode("utf-8")
                
                if key_type == "hash":
                    raw_hash = self.client.hgetall(key)
                    decoded = {}
                    for k, v in raw_hash.items():
                        decoded[k.decode("utf-8") if isinstance(k, bytes) else k] = (
                            v.decode("utf-8") if isinstance(v, bytes) else v
                        )
                    return decoded
                
                elif key_type == "string":
                    val = self.client.get(key)
                    if val:
                        tokens = val.decode("utf-8") if isinstance(val, bytes) else val
                        return {"tokens_remaining": tokens, "burn_rate": "0.0"}
                
                return None
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
                raise
