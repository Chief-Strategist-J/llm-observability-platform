"""Enhanced embedding request handler."""
from typing import List, Dict, Any, Optional
import time
import logging
from services.embedding.text_embedder import TextEmbedder
from services.storage.qdrant_client import QdrantStorage
from core.models.vector_point import VectorPoint
from core.config.settings import settings

logger = logging.getLogger(__name__)

class EmbeddingHandler:
    """Enhanced embedding handler with comprehensive operations."""
    
    def __init__(self):
        self.embedder = TextEmbedder(
            model_name=settings.EMBEDDING_MODEL,
            vector_dim=settings.VECTOR_DIM
        )
        self.storage = QdrantStorage(settings.QDRANT_URL)
        logger.info("EmbeddingHandler initialized")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text."""
        start_time = time.time()
        vector = self.embedder.embed(text)
        elapsed = (time.time() - start_time) * 1000
        logger.debug(f"Generated embedding in {elapsed:.2f}ms")
        return vector
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        start_time = time.time()
        vectors = self.embedder.embed_batch(texts)
        elapsed = (time.time() - start_time) * 1000
        logger.info(f"Generated {len(vectors)} embeddings in {elapsed:.2f}ms")
        return vectors
    
    def store_embeddings(self, collection: str, items: List[dict]) -> Dict[str, Any]:
        """Store text embeddings with detailed response."""
        start_time = time.time()
        
        try:
            # Ensure collection exists
            if not self.storage.collection_exists(collection):
                self.storage.create_collection(collection, settings.VECTOR_DIM, settings.DISTANCE_METRIC)
            
            # Process items
            points = []
            for item in items:
                try:
                    if "vector" in item:
                        vector = item["vector"]
                        if len(vector) != settings.VECTOR_DIM:
                            raise ValueError(f"Vector dimension mismatch: expected {settings.VECTOR_DIM}, got {len(vector)}")
                    else:
                        text = item.get("text", "")
                        vector = self.embedder.embed(text)
                    
                    point = VectorPoint(
                        id=item.get("id"),
                        vector=vector,
                        payload=item.get("payload", {})
                    )
                    points.append(point)
                except Exception as e:
                    logger.error(f"Error processing item {item.get('id', 'unknown')}: {e}")
                    continue
            
            if not points:
                return {"success": False, "message": "No valid points to store"}
            
            # Store points
            success = self.storage.upsert_points(collection, points)
            elapsed = (time.time() - start_time) * 1000
            
            return {
                "success": success,
                "message": f"Processed {len(points)} items in {elapsed:.2f}ms",
                "processed": len(points),
                "failed": len(items) - len(points)
            }
            
        except Exception as e:
            logger.error(f"Error storing embeddings: {e}")
            return {"success": False, "message": str(e)}
    
    def search_similar(
        self,
        collection: str,
        query: str,
        limit: int = 10,
        with_payload: bool = True,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search for similar texts with comprehensive response."""
        start_time = time.time()
        
        try:
            # Generate query embedding
            query_vector = self.embedder.embed(query)
            embed_time = (time.time() - start_time) * 1000
            
            # Perform search
            search_start = time.time()
            results = self.storage.search(
                collection=collection,
                query_vector=query_vector,
                limit=limit,
                with_payload=with_payload,
                score_threshold=score_threshold,
                filter_conditions=filters
            )
            search_time = (time.time() - search_start) * 1000
            total_time = (time.time() - start_time) * 1000
            
            return {
                "results": results,
                "total": len(results),
                "query_time_ms": total_time,
                "embedding_time_ms": embed_time,
                "search_time_ms": search_time,
                "query": query,
                "collection": collection
            }
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return {
                "results": [],
                "total": 0,
                "error": str(e)
            }
    
    def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            info = self.storage.get_collection_info(collection)
            if info:
                return {
                    "exists": True,
                    "name": info["name"],
                    "vectors_count": info["vectors_count"],
                    "segments_count": info["segments_count"],
                    "disk_size_bytes": info["disk_data_size"],
                    "ram_size_bytes": info["ram_data_size"],
                    "vector_config": info["config"]
                }
            else:
                return {"exists": False, "name": collection}
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"exists": False, "error": str(e)}
