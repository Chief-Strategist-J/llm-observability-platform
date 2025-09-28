from typing import List
from services.embedding_service import EmbeddingService
from services.qdrant_service import QdrantService
from core.models import SearchResult

class RAGService:
    def __init__(self):
        self.embedding_service: EmbeddingService = EmbeddingService()
        self.qdrant_service: QdrantService = QdrantService()
    
    def search_and_generate(self, query: str, limit: int = 3) -> dict[str, any]:
        query_embedding: List[float] = self.embedding_service.embed_text(query)
        search_results: List[SearchResult] = self.qdrant_service.search(query_embedding, limit)
        
        if not search_results:
            return {
                "answer": "No relevant documents found.",
                "sources": []
            }
        
        context: str = "\n\n".join([result.text for result in search_results])
        
        answer: str = f"Based on the available documents:\n\n{context}"
        
        sources: List[dict] = [
            {
                "id": result.id,
                "score": result.score,
                "text": result.text[:200] + "..." if len(result.text) > 200 else result.text
            }
            for result in search_results
        ]
        
        return {
            "answer": answer,
            "sources": sources,
            "query": query
        }
