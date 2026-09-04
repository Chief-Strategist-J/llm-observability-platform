import os
import redis
from typing import Optional

_redis_pool: Optional[redis.ConnectionPool] = None

def get_redis_pool(url: Optional[str] = None) -> redis.ConnectionPool:
    global _redis_pool
    if _redis_pool is None:
        redis_url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_pool = redis.ConnectionPool.from_url(redis_url, max_connections=20)
    return _redis_pool

def get_redis_client(url: Optional[str] = None) -> redis.Redis:
    pool = get_redis_pool(url)
    return redis.Redis(connection_pool=pool)
