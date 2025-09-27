"""Qdrant storage client."""
from typing import List, Dict, Any, Optional
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from core.models.vector_point import VectorPoint

logger = logging.getLogger(__name__)

class QdrantStorage:
    def __init__(self, url: str):
        self.client = QdrantClient(url=url)
        self.url = url
        logger.info(f"Connected to Qdrant at {url}")
    
    def create_collection(self, name: str, vector_size: int = 384, distance: str = "Cosine"):
        """Create a new collection."""
        distance_map = {
            "Cosine": Distance.COSINE,
            "Dot": Distance.DOT, 
            "Euclid": Distance.EUCLID
        }
        
        try:
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance_map.get(distance, Distance.COSINE)
                )
            )
            logger.info(f"Created collection: {name}")
            return True
        except Exception as e:
            logger.error(f"Error creating collection {name}: {e}")
            return False
    
    def collection_exists(self, name: str) -> bool:
        """Check if collection exists."""
        try:
            collections = self.client.get_collections()
            return any(c.name == name for c in collections.collections)
        except Exception as e:
            logger.error(f"Error checking collection {name}: {e}")
            return False
    
    def upsert_points(self, collection: str, points: List[VectorPoint]):
        """Insert or update points."""
        qdrant_points = [
            PointStruct(
                id=point.id,
                vector=point.vector,
                payload=point.payload
            ) for point in points
        ]
        
        try:
            self.client.upsert(
                collection_name=collection,
                points=qdrant_points,
                wait=True
            )
            logger.info(f"Upserted {len(points)} points to {collection}")
            return True
        except Exception as e:
            logger.error(f"Error upserting to {collection}: {e}")
            return False
    
    def search(
        self, 
        collection: str, 
        query_vector: List[float], 
        limit: int = 10,
        with_payload: bool = True
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        try:
            results = self.client.query_points(
                collection_name=collection,
                query=query_vector,
                limit=limit,
                with_payload=with_payload
            )
            
            return [
                {
                    "id": str(point.id),
                    "score": float(point.score),
                    "payload": point.payload if with_payload else None
                }
                for point in results.points
            ]
        except Exception as e:
            logger.error(f"Error searching in {collection}: {e}")
            return []
