from abc import ABC, abstractmethod
from typing import List

class EmbeddingModelPort(ABC):
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        raise NotImplementedError

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    @property
    @abstractmethod
    def dimension(self) -> int:
        raise NotImplementedError
