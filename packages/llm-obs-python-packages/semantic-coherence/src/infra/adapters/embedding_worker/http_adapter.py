from __future__ import annotations

import httpx


class EmbeddingWorkerHttpAdapter:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url

    def fetch_embeddings(
        self,
        trace_id: str,
        span_id: str,
    ) -> tuple[list[float] | None, list[float] | None]:
        response = httpx.get(
            f"{self._base_url}/v1/embeddings",
            params={"trace_id": trace_id, "span_id": span_id},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("prompt_embedding"), data.get("response_embedding")
