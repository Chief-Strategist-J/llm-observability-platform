from __future__ import annotations

from typing import Protocol


class EmbeddingStorePort(Protocol):
    def fetch_embeddings(
        self,
        trace_id: str,
        span_id: str,
    ) -> tuple[list[float] | None, list[float] | None]: ...
