from abc import ABC, abstractmethod
from typing import List
from core.domain.models import Chunk, SearchResult

class VectorStorePort(ABC):
    @abstractmethod
    async def upsert(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def search(self, embedding: List[float], limit: int) -> List[SearchResult]:
        raise NotImplementedError
