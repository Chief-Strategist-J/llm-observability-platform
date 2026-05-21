from typing import Protocol, Optional

class EmbeddingClientPort(Protocol):
    async def embed(self, text: str, timeout_seconds: float) -> Optional[list[float]]:
        pass
