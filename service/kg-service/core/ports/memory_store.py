from abc import ABC, abstractmethod

from ..domain.models import Memory, MemoryType


class MemoryStorePort(ABC):
    @abstractmethod
    async def store_memory(self, memory: Memory) -> str:
        pass

    @abstractmethod
    async def retrieve_memories(
        self, query_embedding: list[float], memory_type: MemoryType, limit: int
    ) -> list[Memory]:
        pass

    @abstractmethod
    async def update_memory_access(self, memory_id: str) -> bool:
        pass

    @abstractmethod
    async def decay_memories(self) -> int:
        pass
