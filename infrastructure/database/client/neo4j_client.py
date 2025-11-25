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


class SecureNeo4jClient(BaseSecureClient):
    def __init__(self, config: ConnectionConfig, event_config: Optional[EventConfig] = None):
        logger.debug("neo4j_client_init_start host=%s port=%s", config.host, config.port)
        super().__init__(config, event_config)
        self._driver = None
        logger.info("neo4j_client_initialized")

    def connect(self):
        logger.debug("neo4j_connect_start host=%s port=%s", self.config.host, self.config.port)
        
        with self._connection_lock:
            if self._driver:
                logger.warning("neo4j_already_connected")
                return self
            
            try:
                from neo4j import GraphDatabase
                from neo4j.exceptions import ServiceUnavailable
                
                logger.debug("neo4j_building_uri")
                
                if self.config.security.validate_ssl:
                    uri = f"neo4j+s://{self.config.host}:{self.config.port}"
                    logger.debug("neo4j_uri_built with_ssl=True")
                else:
                    uri = f"bolt://{self.config.host}:{self.config.port}"
                    logger.debug("neo4j_uri_built with_ssl=False")
                
                driver_config = {
                    'max_connection_lifetime': self.config.max_idle_time,
                    'max_connection_pool_size': self.config.pool_size,
                    'connection_acquisition_timeout': self.config.pool_timeout,
                    'connection_timeout': self.config.connection_timeout,
                }
                
                if self.config.security.validate_ssl and self.config.security.ca_path:
                    driver_config['trusted_certificates'] = self.config.security.ca_path
                    logger.debug("neo4j_ssl_ca_configured path=%s", self.config.security.ca_path)
                
                driver_config.update(self.config.extra_params)
                
                logger.debug("neo4j_driver_config_built param_count=%s", len(driver_config))
                
                if self.config.username and self.config.password:
                    encrypted_password = self.config.security.encrypt_value(self.config.password)
                    decrypted_password = self.config.security.decrypt_value(encrypted_password)
                    auth = (self.config.username, decrypted_password)
                    logger.debug("neo4j_auth_configured")
                else:
                    auth = None
                    logger.debug("neo4j_no_auth")
                
                logger.info("neo4j_connecting host=%s port=%s", self.config.host, self.config.port)
                
                self._driver = GraphDatabase.driver(uri, auth=auth, **driver_config)
                
                logger.debug("neo4j_verifying_connectivity")
                self._driver.verify_connectivity()
                
                self._metrics['connections'] += 1
                self._metrics['last_connection'] = time.time()
                
                logger.info("neo4j_connected host=%s port=%s", self.config.host, self.config.port)
                
                if self.event_config.enabled:
                    logger.debug("neo4j_initializing_event_producer")
                    self._init_event_producer()
                    self._publish_event('connected', {
                        'host': self.config.host,
                        'port': self.config.port
                    })
                    logger.debug("neo4j_event_producer_initialized")
                
                return self
                
            except ServiceUnavailable as e:
                self._update_metrics('connect', False, e)
                logger.error("neo4j_connection_failed error=%s", e)
                raise
            except Exception as e:
                self._update_metrics('connect', False, e)
                logger.exception("neo4j_connect_error error=%s", e)
                raise

    def disconnect(self):
        logger.debug("neo4j_disconnect_start")
        
        with self._connection_lock:
            if not self._driver:
                logger.debug("neo4j_not_connected")
                return
            
            try:
                logger.debug("neo4j_closing_driver")
                
                if self.event_config.enabled and self._event_producer:
                    self._publish_event('disconnecting', {
                        'host': self.config.host,
                        'port': self.config.port
                    })
                    logger.debug("neo4j_flushing_events")
                    self._event_producer.flush()
                    self._event_producer.close()
                    logger.debug("neo4j_event_producer_closed")
                
                self._driver.close()
                self._driver = None
                
                logger.info("neo4j_disconnected")
                
            except Exception as e:
                logger.exception("neo4j_disconnect_error error=%s", e)
                raise

    def health_check(self) -> bool:
        logger.debug("neo4j_health_check_start")
        
        if not self._driver:
            logger.warning("neo4j_health_check_no_driver")
            return False
        
        try:
            self._check_rate_limit()
            
            logger.debug("neo4j_health_check_verifying")
            self._driver.verify_connectivity()
            
            logger.info("neo4j_health_check_complete success=True")
            
            self._update_metrics('health_check', True)
            return True
            
        except Exception as e:
            self._update_metrics('health_check', False, e)
            logger.exception("neo4j_health_check_error error=%s", e)
            return False

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        logger.debug("neo4j_execute_query_start query_length=%s param_count=%s",
                    len(query), len(parameters) if parameters else 0)
        
        if not self._driver:
            logger.error("neo4j_execute_query_not_connected")
            raise RuntimeError("Driver not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("neo4j_execute_query_running")
            
            with self._driver.session(database=self.config.database) as session:
                result = session.run(query, parameters or {})
                records = [record.data() for record in result]
            
            logger.info("neo4j_execute_query_complete record_count=%s", len(records))
            
            self._update_metrics('execute_query', True)
            
            if self.event_config.enabled:
                self._publish_event('execute_query', {
                    'record_count': len(records),
                    'has_params': parameters is not None
                })
            
            return records
            
        except Exception as e:
            self._update_metrics('execute_query', False, e)
            logger.exception("neo4j_execute_query_error error=%s", e)
            raise

    def execute_write(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        logger.debug("neo4j_execute_write_start query_length=%s param_count=%s",
                    len(query), len(parameters) if parameters else 0)
        
        if not self._driver:
            logger.error("neo4j_execute_write_not_connected")
            raise RuntimeError("Driver not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("neo4j_execute_write_running")
            
            def _tx_function(tx):
                result = tx.run(query, parameters or {})
                return [record.data() for record in result]
            
            with self._driver.session(database=self.config.database) as session:
                records = session.execute_write(_tx_function)
            
            logger.info("neo4j_execute_write_complete record_count=%s", len(records))
            
            self._update_metrics('execute_write', True)
            
            if self.event_config.enabled:
                self._publish_event('execute_write', {
                    'record_count': len(records),
                    'has_params': parameters is not None
                })
            
            return records
            
        except Exception as e:
            self._update_metrics('execute_write', False, e)
            logger.exception("neo4j_execute_write_error error=%s", e)
            raise

    def create_node(self, label: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        logger.debug("neo4j_create_node_start label=%s property_count=%s", label, len(properties))
        
        try:
            props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
            query = f"CREATE (n:{label} {{{props_str}}}) RETURN n"
            
            logger.debug("neo4j_create_node_executing label=%s", label)
            result = self.execute_write(query, properties)
            
            node = result[0] if result else {}
            logger.info("neo4j_create_node_complete label=%s", label)
            
            return node
            
        except Exception as e:
            logger.exception("neo4j_create_node_error label=%s error=%s", label, e)
            raise

    def find_nodes(self, label: str, properties: Optional[Dict[str, Any]] = None, limit: int = 0) -> List[Dict[str, Any]]:
        logger.debug("neo4j_find_nodes_start label=%s has_props=%s limit=%s",
                    label, properties is not None, limit)
        
        try:
            if properties:
                props_str = " AND ".join([f"n.{k} = ${k}" for k in properties.keys()])
                query = f"MATCH (n:{label}) WHERE {props_str}"
            else:
                query = f"MATCH (n:{label})"
            
            if limit > 0:
                query += f" RETURN n LIMIT {limit}"
            else:
                query += " RETURN n"
            
            logger.debug("neo4j_find_nodes_executing label=%s", label)
            result = self.execute_query(query, properties)
            
            logger.info("neo4j_find_nodes_complete label=%s count=%s", label, len(result))
            
            return result
            
        except Exception as e:
            logger.exception("neo4j_find_nodes_error label=%s error=%s", label, e)
            raise

    def create_relationship(self, from_label: str, from_props: Dict[str, Any], 
                          to_label: str, to_props: Dict[str, Any],
                          rel_type: str, rel_props: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        logger.debug("neo4j_create_relationship_start from_label=%s to_label=%s rel_type=%s",
                    from_label, to_label, rel_type)
        
        try:
            from_props_str = " AND ".join([f"a.{k} = $from_{k}" for k in from_props.keys()])
            to_props_str = " AND ".join([f"b.{k} = $to_{k}" for k in to_props.keys()])
            
            params = {}
            for k, v in from_props.items():
                params[f"from_{k}"] = v
            for k, v in to_props.items():
                params[f"to_{k}"] = v
            
            if rel_props:
                rel_props_str = ", ".join([f"{k}: $rel_{k}" for k in rel_props.keys()])
                for k, v in rel_props.items():
                    params[f"rel_{k}"] = v
                query = f"""
                MATCH (a:{from_label}), (b:{to_label})
                WHERE {from_props_str} AND {to_props_str}
                CREATE (a)-[r:{rel_type} {{{rel_props_str}}}]->(b)
                RETURN r
                """
            else:
                query = f"""
                MATCH (a:{from_label}), (b:{to_label})
                WHERE {from_props_str} AND {to_props_str}
                CREATE (a)-[r:{rel_type}]->(b)
                RETURN r
                """
            
            logger.debug("neo4j_create_relationship_executing")
            result = self.execute_write(query, params)
            
            relationship = result[0] if result else {}
            logger.info("neo4j_create_relationship_complete rel_type=%s", rel_type)
            
            return relationship
            
        except Exception as e:
            logger.exception("neo4j_create_relationship_error rel_type=%s error=%s", rel_type, e)
            raise

