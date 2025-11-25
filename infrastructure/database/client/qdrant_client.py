import logging
from typing import Any, Dict, List, Optional
from database_client_base import BaseSecureClient, ConnectionConfig, EventConfig
import time

logger = logging.getLogger(__name__)


class SecureQdrantClient(BaseSecureClient):
    def __init__(self, config: ConnectionConfig, event_config: Optional[EventConfig] = None):
        logger.debug("qdrant_client_init_start host=%s port=%s", config.host, config.port)
        super().__init__(config, event_config)
        logger.info("qdrant_client_initialized")

    def connect(self):
        logger.debug("qdrant_connect_start host=%s port=%s", self.config.host, self.config.port)
        
        with self._connection_lock:
            if self._client:
                logger.warning("qdrant_already_connected")
                return self
            
            try:
                from qdrant_client import QdrantClient as QC
                from qdrant_client.models import Distance, VectorParams
                
                logger.debug("qdrant_building_client_params")
                
                client_params = {
                    'host': self.config.host,
                    'port': self.config.port,
                    'timeout': self.config.connection_timeout,
                    'prefer_grpc': True,
                }
                
                if self.config.security.token:
                    decrypted_token = self.config.security.decrypt_value(self.config.security.token)
                    client_params['api_key'] = decrypted_token
                    logger.debug("qdrant_api_key_configured")
                
                if self.config.security.validate_ssl:
                    client_params['https'] = True
                    logger.debug("qdrant_https_enabled")
                
                client_params.update(self.config.extra_params)
                
                logger.debug("qdrant_client_params_built param_count=%s", len(client_params))
                
                logger.info("qdrant_connecting host=%s port=%s", self.config.host, self.config.port)
                
                self._client = QC(**client_params)
                
                logger.debug("qdrant_testing_connection")
                self._client.get_collections()
                
                self._metrics['connections'] += 1
                self._metrics['last_connection'] = time.time()
                
                logger.info("qdrant_connected host=%s port=%s", self.config.host, self.config.port)
                
                if self.event_config.enabled:
                    logger.debug("qdrant_initializing_event_producer")
                    self._init_event_producer()
                    self._publish_event('connected', {
                        'host': self.config.host,
                        'port': self.config.port
                    })
                    logger.debug("qdrant_event_producer_initialized")
                
                return self
                
            except Exception as e:
                self._update_metrics('connect', False, e)
                logger.exception("qdrant_connect_error error=%s", e)
                raise

    def disconnect(self):
        logger.debug("qdrant_disconnect_start")
        
        with self._connection_lock:
            if not self._client:
                logger.debug("qdrant_not_connected")
                return
            
            try:
                logger.debug("qdrant_closing_client")
                
                if self.event_config.enabled and self._event_producer:
                    self._publish_event('disconnecting', {
                        'host': self.config.host,
                        'port': self.config.port
                    })
                    logger.debug("qdrant_flushing_events")
                    self._event_producer.flush()
                    self._event_producer.close()
                    logger.debug("qdrant_event_producer_closed")
                
                self._client.close()
                self._client = None
                
                logger.info("qdrant_disconnected")
                
            except Exception as e:
                logger.exception("qdrant_disconnect_error error=%s", e)
                raise

    def health_check(self) -> bool:
        logger.debug("qdrant_health_check_start")
        
        if not self._client:
            logger.warning("qdrant_health_check_no_client")
            return False
        
        try:
            self._check_rate_limit()
            
            logger.debug("qdrant_health_check_listing_collections")
            self._client.get_collections()
            
            logger.info("qdrant_health_check_complete success=True")
            
            self._update_metrics('health_check', True)
            return True
            
        except Exception as e:
            self._update_metrics('health_check', False, e)
            logger.exception("qdrant_health_check_error error=%s", e)
            return False

    def create_collection(self, collection_name: str, vector_size: int, distance: str = "Cosine"):
        logger.debug("qdrant_create_collection_start name=%s vector_size=%s distance=%s",
                    collection_name, vector_size, distance)
        
        if not self._client:
            logger.error("qdrant_create_collection_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            from qdrant_client.models import Distance, VectorParams
            
            distance_map = {
                "Cosine": Distance.COSINE,
                "Euclidean": Distance.EUCLID,
                "Dot": Distance.DOT,
            }
            
            logger.debug("qdrant_create_collection_executing name=%s", collection_name)
            
            self._client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance_map.get(distance, Distance.COSINE)
                )
            )
            
            logger.info("qdrant_create_collection_complete name=%s", collection_name)
            
            self._update_metrics('create_collection', True)
            
            if self.event_config.enabled:
                self._publish_event('create_collection', {
                    'collection_name': collection_name,
                    'vector_size': vector_size,
                    'distance': distance
                })
            
        except Exception as e:
            self._update_metrics('create_collection', False, e)
            logger.exception("qdrant_create_collection_error name=%s error=%s", collection_name, e)
            raise

    def upsert_points(self, collection_name: str, points: List[Dict[str, Any]]):
        logger.debug("qdrant_upsert_points_start collection=%s point_count=%s",
                    collection_name, len(points))
        
        if not self._client:
            logger.error("qdrant_upsert_points_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            from qdrant_client.models import PointStruct
            
            logger.debug("qdrant_upsert_points_building_structs collection=%s", collection_name)
            
            qdrant_points = [
                PointStruct(
                    id=point["id"],
                    vector=point["vector"],
                    payload=point.get("payload", {})
                )
                for point in points
            ]
            
            logger.debug("qdrant_upsert_points_executing collection=%s", collection_name)
            
            self._client.upsert(collection_name=collection_name, points=qdrant_points)
            
            logger.info("qdrant_upsert_points_complete collection=%s count=%s",
                       collection_name, len(qdrant_points))
            
            self._update_metrics('upsert_points', True)
            
            if self.event_config.enabled:
                self._publish_event('upsert_points', {
                    'collection_name': collection_name,
                    'point_count': len(qdrant_points)
                })
            
        except Exception as e:
            self._update_metrics('upsert_points', False, e)
            logger.exception("qdrant_upsert_points_error collection=%s error=%s", collection_name, e)
            raise

    def search(self, collection_name: str, query_vector: List[float], limit: int = 10, 
               score_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        logger.debug("qdrant_search_start collection=%s vector_dim=%s limit=%s threshold=%s",
                    collection_name, len(query_vector), limit, score_threshold)
        
        if not self._client:
            logger.error("qdrant_search_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("qdrant_search_executing collection=%s", collection_name)
            
            search_params = {
                'collection_name': collection_name,
                'query_vector': query_vector,
                'limit': limit
            }
            
            if score_threshold is not None:
                search_params['score_threshold'] = score_threshold
            
            results = self._client.search(**search_params)
            
            formatted_results = [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload
                }
                for hit in results
            ]
            
            logger.info("qdrant_search_complete collection=%s result_count=%s",
                       collection_name, len(formatted_results))
            
            self._update_metrics('search', True)
            
            if self.event_config.enabled:
                self._publish_event('search', {
                    'collection_name': collection_name,
                    'result_count': len(formatted_results),
                    'limit': limit
                })
            
            return formatted_results
            
        except Exception as e:
            self._update_metrics('search', False, e)
            logger.exception("qdrant_search_error collection=%s error=%s", collection_name, e)
            raise

    def get_collection(self, collection_name: str):
        logger.debug("qdrant_get_collection_start name=%s", collection_name)
        
        if not self._client:
            logger.error("qdrant_get_collection_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("qdrant_get_collection_executing name=%s", collection_name)
            result = self._client.get_collection(collection_name)
            
            logger.info("qdrant_get_collection_complete name=%s", collection_name)
            
            self._update_metrics('get_collection', True)
            
            return result
            
        except Exception as e:
            self._update_metrics('get_collection', False, e)
            logger.exception("qdrant_get_collection_error name=%s error=%s", collection_name, e)
            raise

    def list_collections(self) -> List[str]:
        logger.debug("qdrant_list_collections_start")
        
        if not self._client:
            logger.error("qdrant_list_collections_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("qdrant_list_collections_executing")
            collections = self._client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            logger.info("qdrant_list_collections_complete count=%s", len(collection_names))
            
            self._update_metrics('list_collections', True)
            
            if self.event_config.enabled:
                self._publish_event('list_collections', {
                    'collection_count': len(collection_names)
                })
            
            return collection_names
            
        except Exception as e:
            self._update_metrics('list_collections', False, e)
            logger.exception("qdrant_list_collections_error error=%s", e)
            raise

    def delete_collection(self, collection_name: str):
        logger.debug("qdrant_delete_collection_start name=%s", collection_name)
        
        if not self._client:
            logger.error("qdrant_delete_collection_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("qdrant_delete_collection_executing name=%s", collection_name)
            self._client.delete_collection(collection_name)
            
            logger.info("qdrant_delete_collection_complete name=%s", collection_name)
            
            self._update_metrics('delete_collection', True)
            
            if self.event_config.enabled:
                self._publish_event('delete_collection', {
                    'collection_name': collection_name
                })
            
        except Exception as e:
            self._update_metrics('delete_collection', False, e)
            logger.exception("qdrant_delete_collection_error name=%s error=%s", collection_name, e)
            raise