from abc import ABC, abstractmethod
from typing import List
from core.domain.models import Memory, MemoryType

class MemoryStorePort(ABC):
    @abstractmethod
    async def store_memory(self, memory: Memory) -> str:
        pass
    
    @abstractmethod
    async def retrieve_memories(self, query_embedding: List[float], memory_type: MemoryType, limit: int) -> List[Memory]:
        pass
    
    @abstractmethod
    async def update_memory_access(self, memory_id: str) -> bool:
        pass
    
    @abstractmethod
    async def decay_memories(self) -> int:
        pass
