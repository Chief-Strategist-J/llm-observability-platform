from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter
from typing import List, Dict, Any
import uuid
import gc
from core.config import settings
from core.models import Document, SearchResult

class QdrantService:
    def __init__(self):
        self.client: QdrantClient = QdrantClient(url=settings.QDRANT_URL, timeout=300)
        self._ensure_collection()
    
    def _ensure_collection(self) -> None:
        try:
            self.client.get_collection(settings.COLLECTION_NAME)
        except:
            self.client.create_collection(
                collection_name=settings.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=settings.VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )
    
    def upsert_documents_batch(self, documents: List[Document], embeddings: List[List[float]], batch_size: int = 100) -> bool:
        try:
            total_docs: int = len(documents)
            
            for i in range(0, total_docs, batch_size):
                batch_docs: List[Document] = documents[i:i + batch_size]
                batch_embeddings: List[List[float]] = embeddings[i:i + batch_size]
                
                points: List[PointStruct] = []
                
                for doc, embedding in zip(batch_docs, batch_embeddings):
                    point: PointStruct = PointStruct(
                        id=doc.id,
                        vector=embedding,
                        payload={
                            "text": doc.text,
                            "metadata": doc.metadata
                        }
                    )
                    points.append(point)
                
                self.client.upsert(
                    collection_name=settings.COLLECTION_NAME,
                    points=points,
                    wait=True
                )
                
                points.clear()
                gc.collect()
            
            return True
        except Exception as e:
            print(f"Upsert error: {e}")
            return False
    
    def search(self, query_vector: List[float], limit: int = 5) -> List[SearchResult]:
        try:
            results = self.client.query_points(
                collection_name=settings.COLLECTION_NAME,
                query=query_vector,
                limit=limit,
                with_payload=True
            )
            
            search_results: List[SearchResult] = []
            for point in results.points:
                result: SearchResult = SearchResult(
                    id=str(point.id),
                    text=point.payload["text"],
                    score=float(point.score),
                    metadata=point.payload["metadata"]
                )
                search_results.append(result)
            
            return search_results
        except:
            return []
