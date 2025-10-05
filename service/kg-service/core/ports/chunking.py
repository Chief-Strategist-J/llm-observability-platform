from abc import ABC, abstractmethod
from typing import List
from core.domain.models import Chunk

class ChunkingPort(ABC):
    @abstractmethod
    async def chunk_text(self, text: str, metadata: dict) -> List[Chunk]:
        pass
