import httpx
from typing import Optional
from ...ports import EmbeddingClientPort

class HttpEmbeddingClientAdapter(EmbeddingClientPort):
    def __init__(self, endpoint: str):
        self._endpoint = endpoint

    async def embed(self, text: str, timeout_seconds: float) -> Optional[list[float]]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._endpoint,
                json={"text": text},
                timeout=timeout_seconds
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]
