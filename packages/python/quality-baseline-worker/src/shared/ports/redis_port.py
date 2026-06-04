from typing import Protocol

class RedisPort(Protocol):
    def set_baseline_quality(self, model: str, endpoint: str, prompt_type: str, score: float) -> None: ...
