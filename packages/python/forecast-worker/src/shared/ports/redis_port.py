from typing import Protocol, Optional
from datetime import datetime

class RedisPort(Protocol):
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
        """
        Cache forecast values in Redis.
        """
        ...

    def get_cached_forecast(
        self,
        service: str,
        model: str,
        forecast_time: datetime
    ) -> Optional[dict]:
        """
        Retrieve cached forecast values from Redis.
        """
        ...
