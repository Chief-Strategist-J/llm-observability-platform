from shared.ports.embedding_provider import EmbeddingProviderPort, EmbeddingRequest, EmbeddingResponse


class MockEmbeddingClient(EmbeddingProviderPort):
    def create_embedding(self, request: EmbeddingRequest, *, dimensions: int) -> EmbeddingResponse:
        return EmbeddingResponse(
            embedding_key=f"mock_{request.trace_id}_{request.span_id}",
            dimensions=dimensions,
            provider="mock",
        )
