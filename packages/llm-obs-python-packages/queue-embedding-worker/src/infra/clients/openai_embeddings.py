from shared.ports.embedding_provider import EmbeddingProviderPort, EmbeddingRequest, EmbeddingResponse
from shared.utils.hash import stable_embedding_key


class OpenAIEmbeddingClient(EmbeddingProviderPort):
    def create_embedding(self, request: EmbeddingRequest, *, dimensions: int) -> EmbeddingResponse:
        return EmbeddingResponse(
            embedding_key=stable_embedding_key(request.trace_id, request.span_id, request.text, prefix="emb_"),
            dimensions=dimensions,
            provider="openai",
        )
