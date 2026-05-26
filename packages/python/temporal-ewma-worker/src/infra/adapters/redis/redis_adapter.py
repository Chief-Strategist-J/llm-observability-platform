import redis
from shared.ports.redis_port import RedisPort


class RedisAdapter(RedisPort):
    def __init__(self, url: str):
        self.client = redis.from_url(url)

    def get_ewma(self, service: str, model: str, hour_of_week: int) -> float | None:
        key = f"ewma:cost:{service}:{model}:{hour_of_week}"
        val = self.client.get(key)
        if val is not None:
            if isinstance(val, (str, bytes)):
                return float(val)
        return None

    def set_ewma(
        self, service: str, model: str, hour_of_week: int, value: float
    ) -> None:
        key = f"ewma:cost:{service}:{model}:{hour_of_week}"
        self.client.set(key, str(value))
