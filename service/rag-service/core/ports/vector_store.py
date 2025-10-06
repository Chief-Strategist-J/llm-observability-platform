from abc import ABC, abstractmethod

from core.domain.models import Chunk, SearchResult


class VectorStorePort(ABC):
    @abstractmethod
    async def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def search(self, embedding: list[float], limit: int) -> list[SearchResult]:
        raise NotImplementedError
