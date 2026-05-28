from abc import ABC, abstractmethod
from typing import Optional

class RedisPort(ABC):
    @abstractmethod
    def invalidate_budget_cache(self, user_id: str, model: str) -> None:
        pass

    @abstractmethod
    def get_token_bucket_status(self, user_id: str, model: str) -> Optional[dict]:
        pass
