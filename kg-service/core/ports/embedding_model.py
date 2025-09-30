from abc import ABC, abstractmethod
from typing import List

class EmbeddingModelPort(ABC):
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        pass
