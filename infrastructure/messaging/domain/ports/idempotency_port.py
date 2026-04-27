from abc import ABC, abstractmethod


class IdempotencyPort(ABC):
    @abstractmethod
    async def check_and_store(self, event_id: str) -> bool:
        pass

    @abstractmethod
    async def exists(self, event_id: str) -> bool:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass
