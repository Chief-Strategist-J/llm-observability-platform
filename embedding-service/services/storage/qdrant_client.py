"""Enhanced Qdrant storage client with full API support."""
from typing import List, Dict, Any, Optional, Union
import logging
import time
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http.exceptions import UnexpectedResponse, ResponseHandlingException
from core.models.vector_point import VectorPoint

logger = logging.getLogger(__name__)

class QdrantStorage:
    """Enhanced Qdrant storage client supporting all major operations."""
    
    def __init__(self, url: str):
        self.url = url
        self.client = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Qdrant with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.client = QdrantClient(url=self.url, timeout=30)
                # Test connection
                self.client.get_collections()
                logger.info(f"Connected to Qdrant at {self.url}")
                return
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise ConnectionError(f"Failed to connect to Qdrant after {max_retries} attempts")
                time.sleep(2)
    
    def _get_distance_enum(self, distance: str) -> Distance:
        """Convert string to Qdrant Distance enum."""
        distance_map = {
            "Cosine": Distance.COSINE,
            "Dot": Distance.DOT, 
            "Euclid": Distance.EUCLID,
            "Manhattan": Distance.MANHATTAN
        }
        return distance_map.get(distance.upper().title(), Distance.COSINE)
    
    def create_collection(self, name: str, vector_size: int = 384, distance: str = "Cosine") -> bool:
        """Create a new collection."""
        try:
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=self._get_distance_enum(distance)
                )
            )
            logger.info(f"Created collection: {name} (size={vector_size}, distance={distance})")
            return True
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"Collection {name} already exists")
                return True
            logger.error(f"Error creating collection {name}: {e}")
            return False
    
    def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        try:
            self.client.delete_collection(collection_name=name)
            logger.info(f"Deleted collection: {name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection {name}: {e}")
            return False
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections."""
        try:
            collections = self.client.get_collections()
            return [
                {
                    "name": c.name,
                    "vectors_count": getattr(c, 'vectors_count', 0),
                    "segments_count": getattr(c, 'segments_count', 0)
                }
                for c in collections.collections
            ]
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []
    
    def collection_exists(self, name: str) -> bool:
        """Check if collection exists."""
        try:
            collections = self.client.get_collections()
            return any(c.name == name for c in collections.collections)
        except Exception as e:
            logger.error(f"Error checking collection {name}: {e}")
            return False
    
    def get_collection_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed collection information."""
        try:
            info = self.client.get_collection(collection_name=name)
            return {
                "name": name,
                "vectors_count": info.vectors_count,
                "segments_count": info.segments_count,
                "disk_data_size": info.disk_data_size,
                "ram_data_size": info.ram_data_size,
                "config": {
                    "distance": info.config.params.vectors.distance.value,
                    "vector_size": info.config.params.vectors.size
                }
            }
        except Exception as e:
            logger.error(f"Error getting collection info for {name}: {e}")
            return None
    
    def upsert_points(self, collection: str, points: List[VectorPoint]) -> bool:
        """Insert or update points."""
        try:
            qdrant_points = [
                PointStruct(
                    id=point.id,
                    vector=point.vector,
                    payload=point.payload
                ) for point in points
            ]
            
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
        with_payload: bool = True,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors with optional filtering."""
        try:
            # Build filter if provided
            query_filter = None
            if filter_conditions:
                # Simple filter support - extend as needed
                conditions = []
                for key, value in filter_conditions.items():
                    conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
                query_filter = Filter(must=conditions)
            
            results = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=limit,
                with_payload=with_payload,
                score_threshold=score_threshold,
                query_filter=query_filter
            )
            
            return [
                {
                    "id": str(point.id),
                    "score": float(point.score),
                    "payload": point.payload if with_payload else None
                }
                for point in results
            ]
        except Exception as e:
            logger.error(f"Error searching in {collection}: {e}")
            return []
    
    def get_point(self, collection: str, point_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """Get a specific point by ID."""
        try:
            point = self.client.retrieve(
                collection_name=collection,
                ids=[point_id],
                with_payload=True,
                with_vectors=True
            )
            if point:
                p = point[0]
                return {
                    "id": str(p.id),
                    "vector": p.vector,
                    "payload": p.payload
                }
            return None
        except Exception as e:
            logger.error(f"Error getting point {point_id} from {collection}: {e}")
            return None
    
    def delete_points(self, collection: str, point_ids: List[Union[str, int]]) -> bool:
        """Delete specific points."""
        try:
            self.client.delete(
                collection_name=collection,
                points_selector=point_ids,
                wait=True
            )
            logger.info(f"Deleted {len(point_ids)} points from {collection}")
            return True
        except Exception as e:
            logger.error(f"Error deleting points from {collection}: {e}")
            return False
    
    def count_points(self, collection: str) -> int:
        """Count total points in collection."""
        try:
            info = self.client.get_collection(collection_name=collection)
            return info.vectors_count
        except Exception as e:
            logger.error(f"Error counting points in {collection}: {e}")
            return 0
