from services.rag.api.rag_service import RAGService
from services.rag.retrieval.vector_search import ChromaRetriever
from services.rag.retrieval.reranker import CrossEncoderReranker
from services.rag.indexing.embedder_adapter import SentenceTransformerEmbedder
from services.rag.ingestion.pipeline import IngestionPipeline
from services.shared.cache import instance_cache


def get_rag_service() -> RAGService:
    """Acquire the RAG service instance, using the cache for singleton behavior."""
    cached = instance_cache.get("rag_service")
    if cached is not None:
        return cached
    
    embedder = SentenceTransformerEmbedder()
    lc_embeddings = embedder.as_langchain_embeddings()
    retriever = ChromaRetriever(lc_embeddings)
    ingestion = IngestionPipeline(store=retriever)
    reranker = CrossEncoderReranker()
    
    service = RAGService(
        retriever=retriever,
        store=retriever,
        ingestion=ingestion,
        reranker=reranker,
    )
    
    instance_cache.set("rag_service", service)
    return service
