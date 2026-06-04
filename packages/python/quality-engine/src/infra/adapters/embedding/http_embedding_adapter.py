from __future__ import annotations
import json
import asyncio
import httpx

from shared.ports.embedding_client_port import EmbeddingClientPort


class HttpEmbeddingClientAdapter(EmbeddingClientPort):
    """
    F-Q-04: Calls embedding-worker POST /embed with 500ms timeout.
    Returns None on timeout — coherence_score will be null, processing continues.
    """

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def embed(self, text: str, timeout_ms: int = 500) -> list[float] | None:
        timeout_s = timeout_ms / 1000.0
        try:
            async with httpx.AsyncClient(timeout=timeout_s) as client:
                response = await client.post(
                    f"{self._base_url}/embed",
                    json={"text": text},
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                data = response.json()
                return list(data["embedding"])
        except (httpx.TimeoutException, httpx.HTTPError, KeyError, Exception):
            return None
