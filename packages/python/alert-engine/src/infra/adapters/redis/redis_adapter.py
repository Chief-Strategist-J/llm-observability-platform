import time
import redis
from shared.ports.redis_port import RedisPort

class RedisAdapter(RedisPort):
    def __init__(self, redis_url: str):
        self.client = redis.from_url(redis_url)

    def acquire_rate_limit(self, key: str, ttl_seconds: int) -> bool:
        res = self.client.set(key, str(time.time()), nx=True, ex=ttl_seconds)
        return res is not None
