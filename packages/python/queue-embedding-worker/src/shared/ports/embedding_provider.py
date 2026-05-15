from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EmbeddingRequest:
    text: str
    model: str
    trace_id: str
    span_id: str


@dataclass(frozen=True)
class EmbeddingResponse:
    embedding_key: str
    dimensions: int
    provider: str


class EmbeddingProviderPort(Protocol):
    def create_embedding(self, request: EmbeddingRequest, *, dimensions: int) -> EmbeddingResponse: ...
