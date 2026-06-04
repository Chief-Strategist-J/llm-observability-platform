import redis
from shared.ports.redis_port import RedisPort

class RedisAdapter(RedisPort):
    def __init__(self, url: str):
        self.client = redis.from_url(url)

    def set_baseline_quality(self, model: str, endpoint: str, prompt_type: str, score: float) -> None:
        key = f"baseline:quality:{model}:{endpoint}:{prompt_type}"
        self.client.set(key, str(score))
