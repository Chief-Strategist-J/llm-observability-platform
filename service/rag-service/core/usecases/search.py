import logging

from ..domain.models import QueryRequest
from ..ports.embedding_model import EmbeddingModelPort
from ..ports.vector_store import VectorStorePort

logger = logging.getLogger(__name__)


async def search_documents(
    request: QueryRequest, embedder: EmbeddingModelPort, vector_store: VectorStorePort
) -> dict:
    logger.info(f"Search: {request.query[:50]}")

    query_embedding = await embedder.embed_text(request.query)
    results = await vector_store.search(query_embedding, request.limit)

    if not results:
        return {"query": request.query, "answer": "No documents found", "sources": []}

    context = "\n\n".join([r.chunk.text for r in results[:3]])
    answer = f"Based on documents:\n\n{context[:800]}..."

    return {
        "query": request.query,
        "answer": answer,
        "sources": [
            {
                "text": r.chunk.text[:300],
                "score": round(r.score, 3),
                "metadata": r.chunk.metadata,
            }
            for r in results
        ],
    }
