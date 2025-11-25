import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import logging
from typing import Any, Dict, List, Optional
from infrastructure.database.client.base_client import BaseSecureClient, ConnectionConfig, EventConfig
import time

logger = logging.getLogger(__name__)


class SecureMongoDBClient(BaseSecureClient):
    def __init__(self, config: ConnectionConfig, event_config: Optional[EventConfig] = None):
        logger.debug("mongodb_client_init_start host=%s port=%s", config.host, config.port)
        super().__init__(config, event_config)
        self._db = None
        logger.info("mongodb_client_initialized")

    def connect(self):
        logger.debug("mongodb_connect_start host=%s port=%s", self.config.host, self.config.port)
        
        with self._connection_lock:
            if self._client:
                logger.warning("mongodb_already_connected")
                return self
            
            try:
                from pymongo import MongoClient
                from pymongo.errors import ConnectionFailure
                
                logger.debug("mongodb_building_connection_string")
                
                auth_source = self.config.auth_database or "admin"
                
                connection_params = {
                    'serverSelectionTimeoutMS': self.config.connection_timeout * 1000,
                    'socketTimeoutMS': self.config.socket_timeout * 1000,
                    'maxPoolSize': self.config.pool_size,
                    'minPoolSize': max(1, self.config.pool_size // 4),
                    'maxIdleTimeMS': self.config.max_idle_time * 1000,
                    'retryWrites': self.config.retry_writes,
                    'retryReads': self.config.retry_reads,
                    'compressors': 'snappy,zlib,zstd',
                }
                
                if self.config.security.validate_ssl:
                    connection_params['tls'] = True
                    if self.config.security.ca_path:
                        connection_params['tlsCAFile'] = self.config.security.ca_path
                        logger.debug("mongodb_tls_ca_configured path=%s", self.config.security.ca_path)
                    if self.config.security.cert_path:
                        connection_params['tlsCertificateKeyFile'] = self.config.security.cert_path
                        logger.debug("mongodb_tls_cert_configured path=%s", self.config.security.cert_path)
                
                connection_params.update(self.config.extra_params)
                
                logger.debug("mongodb_connection_params_built param_count=%s", len(connection_params))
                
                if self.config.username and self.config.password:
                    encrypted_password = self.config.security.encrypt_value(self.config.password)
                    decrypted_password = self.config.security.decrypt_value(encrypted_password)
                    
                    connection_string = (
                        f"mongodb://{self.config.username}:{decrypted_password}@"
                        f"{self.config.host}:{self.config.port}/?authSource={auth_source}"
                    )
                    logger.debug("mongodb_connection_string_built with_auth=True")
                else:
                    connection_string = f"mongodb://{self.config.host}:{self.config.port}/"
                    logger.debug("mongodb_connection_string_built with_auth=False")
                
                logger.info("mongodb_connecting host=%s port=%s", self.config.host, self.config.port)
                
                self._client = MongoClient(connection_string, **connection_params)
                
                logger.debug("mongodb_testing_connection")
                self._client.admin.command('ping')
                
                if self.config.database:
                    logger.debug("mongodb_selecting_database db=%s", self.config.database)
                    self._db = self._client[self.config.database]
                    logger.debug("mongodb_database_selected")
                
                self._metrics['connections'] += 1
                self._metrics['last_connection'] = time.time()
                
                logger.info("mongodb_connected host=%s port=%s db=%s",
                           self.config.host, self.config.port, self.config.database)
                
                if self.event_config.enabled:
                    logger.debug("mongodb_initializing_event_producer")
                    self._init_event_producer()
                    self._publish_event('connected', {
                        'host': self.config.host,
                        'port': self.config.port,
                        'database': self.config.database
                    })
                    logger.debug("mongodb_event_producer_initialized")
                
                return self
                
            except ConnectionFailure as e:
                self._update_metrics('connect', False, e)
                logger.error("mongodb_connection_failed error=%s", e)
                raise
            except Exception as e:
                self._update_metrics('connect', False, e)
                logger.exception("mongodb_connect_error error=%s", e)
                raise

    def disconnect(self):
        logger.debug("mongodb_disconnect_start")
        
        with self._connection_lock:
            if not self._client:
                logger.debug("mongodb_not_connected")
                return
            
            try:
                logger.debug("mongodb_closing_connection")
                
                if self.event_config.enabled and self._event_producer:
                    self._publish_event('disconnecting', {
                        'host': self.config.host,
                        'port': self.config.port
                    })
                    logger.debug("mongodb_flushing_events")
                    self._event_producer.flush()
                    self._event_producer.close()
                    logger.debug("mongodb_event_producer_closed")
                
                self._client.close()
                self._client = None
                self._db = None
                
                logger.info("mongodb_disconnected")
                
            except Exception as e:
                logger.exception("mongodb_disconnect_error error=%s", e)
                raise

    def health_check(self) -> bool:
        logger.debug("mongodb_health_check_start")
        
        if not self._client:
            logger.warning("mongodb_health_check_no_client")
            return False
        
        try:
            self._check_rate_limit()
            
            logger.debug("mongodb_health_check_executing_ping")
            result = self._client.admin.command('ping')
            
            success = result.get('ok') == 1
            logger.info("mongodb_health_check_complete success=%s", success)
            
            self._update_metrics('health_check', success)
            return success
            
        except Exception as e:
            self._update_metrics('health_check', False, e)
            logger.exception("mongodb_health_check_error error=%s", e)
            return False

    def get_database(self, db_name: str):
        logger.debug("mongodb_get_database_start db_name=%s", db_name)
        
        if not self._client:
            logger.error("mongodb_get_database_not_connected")
            raise RuntimeError("Client not connected")
        
        logger.info("mongodb_get_database_complete db_name=%s", db_name)
        return self._client[db_name]

    def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        logger.debug("mongodb_insert_one_start collection=%s doc_keys=%s",
                    collection, list(document.keys()))
        
        if not self._db:
            logger.error("mongodb_insert_one_no_database")
            raise RuntimeError("No database selected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("mongodb_insert_one_executing collection=%s", collection)
            result = self._db[collection].insert_one(document)
            doc_id = str(result.inserted_id)
            
            logger.info("mongodb_insert_one_success collection=%s doc_id=%s", collection, doc_id)
            
            self._update_metrics('insert_one', True)
            
            if self.event_config.enabled:
                self._publish_event('insert_one', {
                    'collection': collection,
                    'document_id': doc_id,
                    'field_count': len(document)
                })
            
            return doc_id
            
        except Exception as e:
            self._update_metrics('insert_one', False, e)
            logger.exception("mongodb_insert_one_error collection=%s error=%s", collection, e)
            raise

    def insert_many(self, collection: str, documents: List[Dict[str, Any]]) -> List[str]:
        logger.debug("mongodb_insert_many_start collection=%s doc_count=%s",
                    collection, len(documents))
        
        if not self._db:
            logger.error("mongodb_insert_many_no_database")
            raise RuntimeError("No database selected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("mongodb_insert_many_executing collection=%s", collection)
            result = self._db[collection].insert_many(documents)
            doc_ids = [str(id) for id in result.inserted_ids]
            
            logger.info("mongodb_insert_many_success collection=%s count=%s",
                       collection, len(doc_ids))
            
            self._update_metrics('insert_many', True)
            
            if self.event_config.enabled:
                self._publish_event('insert_many', {
                    'collection': collection,
                    'count': len(doc_ids)
                })
            
            return doc_ids
            
        except Exception as e:
            self._update_metrics('insert_many', False, e)
            logger.exception("mongodb_insert_many_error collection=%s error=%s", collection, e)
            raise

    def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        logger.debug("mongodb_find_one_start collection=%s query_keys=%s",
                    collection, list(query.keys()))
        
        if not self._db:
            logger.error("mongodb_find_one_no_database")
            raise RuntimeError("No database selected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("mongodb_find_one_executing collection=%s", collection)
            result = self._db[collection].find_one(query)
            
            found = result is not None
            logger.info("mongodb_find_one_complete collection=%s found=%s", collection, found)
            
            self._update_metrics('find_one', True)
            
            if self.event_config.enabled:
                self._publish_event('find_one', {
                    'collection': collection,
                    'found': found
                })
            
            return result
            
        except Exception as e:
            self._update_metrics('find_one', False, e)
            logger.exception("mongodb_find_one_error collection=%s error=%s", collection, e)
            raise

    def find_many(self, collection: str, query: Dict[str, Any], limit: int = 0) -> List[Dict[str, Any]]:
        logger.debug("mongodb_find_many_start collection=%s query_keys=%s limit=%s",
                    collection, list(query.keys()), limit)
        
        if not self._db:
            logger.error("mongodb_find_many_no_database")
            raise RuntimeError("No database selected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("mongodb_find_many_executing collection=%s", collection)
            cursor = self._db[collection].find(query)
            
            if limit > 0:
                logger.debug("mongodb_find_many_limiting limit=%s", limit)
                cursor = cursor.limit(limit)
            
            results = list(cursor)
            
            logger.info("mongodb_find_many_complete collection=%s count=%s",
                       collection, len(results))
            
            self._update_metrics('find_many', True)
            
            if self.event_config.enabled:
                self._publish_event('find_many', {
                    'collection': collection,
                    'count': len(results),
                    'limit': limit
                })
            
            return results
            
        except Exception as e:
            self._update_metrics('find_many', False, e)
            logger.exception("mongodb_find_many_error collection=%s error=%s", collection, e)
            raise

    def update_one(self, collection: str, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        logger.debug("mongodb_update_one_start collection=%s query_keys=%s update_keys=%s",
                    collection, list(query.keys()), list(update.keys()))
        
        if not self._db:
            logger.error("mongodb_update_one_no_database")
            raise RuntimeError("No database selected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("mongodb_update_one_executing collection=%s", collection)
            result = self._db[collection].update_one(query, {"$set": update})
            count = result.modified_count
            
            logger.info("mongodb_update_one_complete collection=%s modified=%s", collection, count)
            
            self._update_metrics('update_one', True)
            
            if self.event_config.enabled:
                self._publish_event('update_one', {
                    'collection': collection,
                    'modified_count': count
                })
            
            return count
            
        except Exception as e:
            self._update_metrics('update_one', False, e)
            logger.exception("mongodb_update_one_error collection=%s error=%s", collection, e)
            raise

    def update_many(self, collection: str, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        logger.debug("mongodb_update_many_start collection=%s query_keys=%s update_keys=%s",
                    collection, list(query.keys()), list(update.keys()))
        
        if not self._db:
            logger.error("mongodb_update_many_no_database")
            raise RuntimeError("No database selected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("mongodb_update_many_executing collection=%s", collection)
            result = self._db[collection].update_many(query, {"$set": update})
            count = result.modified_count
            
            logger.info("mongodb_update_many_complete collection=%s modified=%s", collection, count)
            
            self._update_metrics('update_many', True)
            
            if self.event_config.enabled:
                self._publish_event('update_many', {
                    'collection': collection,
                    'modified_count': count
                })
            
            return count
            
        except Exception as e:
            self._update_metrics('update_many', False, e)
            logger.exception("mongodb_update_many_error collection=%s error=%s", collection, e)
            raise

    def delete_one(self, collection: str, query: Dict[str, Any]) -> int:
        logger.debug("mongodb_delete_one_start collection=%s query_keys=%s",
                    collection, list(query.keys()))
        
        if not self._db:
            logger.error("mongodb_delete_one_no_database")
            raise RuntimeError("No database selected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("mongodb_delete_one_executing collection=%s", collection)
            result = self._db[collection].delete_one(query)
            count = result.deleted_count
            
            logger.info("mongodb_delete_one_complete collection=%s deleted=%s", collection, count)
            
            self._update_metrics('delete_one', True)
            
            if self.event_config.enabled:
                self._publish_event('delete_one', {
                    'collection': collection,
                    'deleted_count': count
                })
            
            return count
            
        except Exception as e:
            self._update_metrics('delete_one', False, e)
            logger.exception("mongodb_delete_one_error collection=%s error=%s", collection, e)
            raise

    def delete_many(self, collection: str, query: Dict[str, Any]) -> int:
        logger.debug("mongodb_delete_many_start collection=%s query_keys=%s",
                    collection, list(query.keys()))
        
        if not self._db:
            logger.error("mongodb_delete_many_no_database")
            raise RuntimeError("No database selected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("mongodb_delete_many_executing collection=%s", collection)
            result = self._db[collection].delete_many(query)
            count = result.deleted_count
            
            logger.info("mongodb_delete_many_complete collection=%s deleted=%s", collection, count)
            
            self._update_metrics('delete_many', True)
            
            if self.event_config.enabled:
                self._publish_event('delete_many', {
                    'collection': collection,
                    'deleted_count': count
                })
            
            return count
            
        except Exception as e:
            self._update_metrics('delete_many', False, e)
            logger.exception("mongodb_delete_many_error collection=%s error=%s", collection, e)
            raise

    def aggregate(self, collection: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        logger.debug("mongodb_aggregate_start collection=%s pipeline_stages=%s",
                    collection, len(pipeline))
        
        if not self._db:
            logger.error("mongodb_aggregate_no_database")
            raise RuntimeError("No database selected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("mongodb_aggregate_executing collection=%s", collection)
            results = list(self._db[collection].aggregate(pipeline))
            
            logger.info("mongodb_aggregate_complete collection=%s result_count=%s",
                       collection, len(results))
            
            self._update_metrics('aggregate', True)
            
            if self.event_config.enabled:
                self._publish_event('aggregate', {
                    'collection': collection,
                    'pipeline_stages': len(pipeline),
                    'result_count': len(results)
                })
            
            return results
            
        except Exception as e:
            self._update_metrics('aggregate', False, e)
            logger.exception("mongodb_aggregate_error collection=%s error=%s", collection, e)
            raise

    def create_index(self, collection: str, keys: List[tuple], unique: bool = False) -> str:
        logger.debug("mongodb_create_index_start collection=%s keys=%s unique=%s",
                    collection, keys, unique)
        
        if not self._db:
            logger.error("mongodb_create_index_no_database")
            raise RuntimeError("No database selected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("mongodb_create_index_executing collection=%s", collection)
            index_name = self._db[collection].create_index(keys, unique=unique)
            
            logger.info("mongodb_create_index_complete collection=%s index=%s",
                       collection, index_name)
            
            self._update_metrics('create_index', True)
            
            if self.event_config.enabled:
                self._publish_event('create_index', {
                    'collection': collection,
                    'index_name': index_name,
                    'unique': unique
                })
            
            return index_name
            
        except Exception as e:
            self._update_metrics('create_index', False, e)
            logger.exception("mongodb_create_index_error collection=%s error=%s", collection, e)
            raise