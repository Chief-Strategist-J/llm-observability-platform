from abc import ABC, abstractmethod
from typing import Any
from domain.ports.database_port import EventRecord


class PersistenceStrategy(ABC):
    @abstractmethod
    async def save(self, event: EventRecord) -> str:
        pass

    @abstractmethod
    async def save_batch(self, events: list) -> list:
        pass
