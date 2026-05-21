from typing import Optional
from .ports import EmbeddingClientPort

class MiniLMEmbeddingService:
    def __init__(self, client: EmbeddingClientPort):
        self._client = client

    async def get_embedding(self, text: str) -> Optional[list[float]]:
        try:
            return await self._client.embed(text, timeout_seconds=0.5)
        except Exception:
            return None
