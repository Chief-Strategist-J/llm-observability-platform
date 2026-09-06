from __future__ import annotations
from typing import Protocol


class EmbeddingClientPort(Protocol):
    """Port for fetching embeddings from embedding-worker when not present on span."""

    async def embed(self, text: str, timeout_ms: int = 500) -> list[float] | None:
        """Returns embedding vector or None on timeout."""
        ...
