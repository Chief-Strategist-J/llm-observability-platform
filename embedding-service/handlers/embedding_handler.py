"""Embedding request handlers."""
from typing import List
from services.embedding.text_embedder import TextEmbedder
from services.storage.qdrant_client import QdrantStorage
from core.models.vector_point import VectorPoint
from core.config.settings import settings

class EmbeddingHandler:
    def __init__(self):
        self.embedder = TextEmbedder(
            model_name=settings.EMBEDDING_MODEL,
            vector_dim=settings.VECTOR_DIM
        )
        self.storage = QdrantStorage(settings.QDRANT_URL)
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text."""
        return self.embedder.embed(text)
    
    def store_embeddings(self, collection: str, items: List[dict]) -> bool:
        """Store text embeddings."""
        points = []
        for item in items:
            text = item.get("text", "")
            vector = self.embedder.embed(text)
            point = VectorPoint(
                id=item.get("id"),
                vector=vector,
                payload=item.get("payload", {})
            )
            points.append(point)
        
        return self.storage.upsert_points(collection, points)
    
    def search_similar(
        self, 
        collection: str, 
        query: str, 
        limit: int = 10,
        with_payload: bool = True
    ):
        """Search for similar texts."""
        query_vector = self.embedder.embed(query)
        return self.storage.search(collection, query_vector, limit, with_payload)
