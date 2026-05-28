from abc import ABC, abstractmethod

class MetricsPort(ABC):
    @abstractmethod
    def record_request(self, method: str, path: str, status_code: int) -> None:
        pass

    @abstractmethod
    def record_invalidation(self, user_id: str, model: str) -> None:
        pass
