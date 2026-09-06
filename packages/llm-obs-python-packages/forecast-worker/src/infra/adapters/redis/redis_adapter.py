import json
import redis
from datetime import datetime
from typing import Optional
from shared.ports.redis_port import RedisPort

class RedisAdapter(RedisPort):
    def __init__(self, url: str) -> None:
        self.client = redis.from_url(url)

    def cache_forecast(
        self,
        service: str,
        model: str,
        forecast_time: datetime,
        mean: float,
        p10: float,
        p90: float,
        ttl_seconds: int = 3600
    ) -> None:
        key = f"forecast:{service}:{model}:{forecast_time.isoformat()}"
        data = {
            "mean": mean,
            "p10": p10,
            "p90": p90,
            "timestamp": forecast_time.isoformat()
        }
        self.client.setex(key, ttl_seconds, json.dumps(data))

    def get_cached_forecast(
        self,
        service: str,
        model: str,
        forecast_time: datetime
    ) -> Optional[dict]:
        key = f"forecast:{service}:{model}:{forecast_time.isoformat()}"
        val = self.client.get(key)
        if val:
            try:
                return json.loads(val)
            except Exception:
                return None
        return None
