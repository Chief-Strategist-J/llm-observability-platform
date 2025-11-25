import logging
from typing import Any, Dict, List, Optional, Union
from database_client_base import BaseSecureClient, ConnectionConfig, EventConfig
import time

logger = logging.getLogger(__name__)


class SecureRedisClient(BaseSecureClient):
    def __init__(self, config: ConnectionConfig, event_config: Optional[EventConfig] = None):
        logger.debug("redis_client_init_start host=%s port=%s", config.host, config.port)
        super().__init__(config, event_config)
        logger.info("redis_client_initialized")

    def connect(self):
        logger.debug("redis_connect_start host=%s port=%s", self.config.host, self.config.port)
        
        with self._connection_lock:
            if self._client:
                logger.warning("redis_already_connected")
                return self
            
            try:
                import redis
                from redis.exceptions import ConnectionError
                
                logger.debug("redis_building_connection_params")
                
                connection_params = {
                    'host': self.config.host,
                    'port': self.config.port,
                    'db': int(self.config.database or 0),
                    'decode_responses': True,
                    'socket_timeout': self.config.socket_timeout,
                    'socket_connect_timeout': self.config.connection_timeout,
                    'socket_keepalive': True,
                    'health_check_interval': 30,
                    'retry_on_timeout': True,
                    'max_connections': self.config.pool_size,
                }
                
                if self.config.password:
                    encrypted_password = self.config.security.encrypt_value(self.config.password)
                    decrypted_password = self.config.security.decrypt_value(encrypted_password)
                    connection_params['password'] = decrypted_password
                    logger.debug("redis_password_configured")
                
                if self.config.security.validate_ssl:
                    connection_params['ssl'] = True
                    if self.config.security.ca_path:
                        connection_params['ssl_ca_certs'] = self.config.security.ca_path
                        logger.debug("redis_ssl_ca_configured path=%s", self.config.security.ca_path)
                    if self.config.security.cert_path:
                        connection_params['ssl_certfile'] = self.config.security.cert_path
                        logger.debug("redis_ssl_cert_configured path=%s", self.config.security.cert_path)
                    if self.config.security.key_path:
                        connection_params['ssl_keyfile'] = self.config.security.key_path
                        logger.debug("redis_ssl_key_configured path=%s", self.config.security.key_path)
                
                connection_params.update(self.config.extra_params)
                
                logger.debug("redis_connection_params_built param_count=%s", len(connection_params))
                
                logger.info("redis_connecting host=%s port=%s db=%s",
                           self.config.host, self.config.port, connection_params['db'])
                
                self._client = redis.Redis(**connection_params)
                
                logger.debug("redis_testing_connection")
                self._client.ping()
                
                self._metrics['connections'] += 1
                self._metrics['last_connection'] = time.time()
                
                logger.info("redis_connected host=%s port=%s db=%s",
                           self.config.host, self.config.port, connection_params['db'])
                
                if self.event_config.enabled:
                    logger.debug("redis_initializing_event_producer")
                    self._init_event_producer()
                    self._publish_event('connected', {
                        'host': self.config.host,
                        'port': self.config.port,
                        'db': connection_params['db']
                    })
                    logger.debug("redis_event_producer_initialized")
                
                return self
                
            except ConnectionError as e:
                self._update_metrics('connect', False, e)
                logger.error("redis_connection_failed error=%s", e)
                raise
            except Exception as e:
                self._update_metrics('connect', False, e)
                logger.exception("redis_connect_error error=%s", e)
                raise

    def disconnect(self):
        logger.debug("redis_disconnect_start")
        
        with self._connection_lock:
            if not self._client:
                logger.debug("redis_not_connected")
                return
            
            try:
                logger.debug("redis_closing_connection")
                
                if self.event_config.enabled and self._event_producer:
                    self._publish_event('disconnecting', {
                        'host': self.config.host,
                        'port': self.config.port
                    })
                    logger.debug("redis_flushing_events")
                    self._event_producer.flush()
                    self._event_producer.close()
                    logger.debug("redis_event_producer_closed")
                
                self._client.close()
                self._client = None
                
                logger.info("redis_disconnected")
                
            except Exception as e:
                logger.exception("redis_disconnect_error error=%s", e)
                raise

    def health_check(self) -> bool:
        logger.debug("redis_health_check_start")
        
        if not self._client:
            logger.warning("redis_health_check_no_client")
            return False
        
        try:
            self._check_rate_limit()
            
            logger.debug("redis_health_check_executing_ping")
            result = self._client.ping()
            
            success = result is True
            logger.info("redis_health_check_complete success=%s", success)
            
            self._update_metrics('health_check', success)
            return success
            
        except Exception as e:
            self._update_metrics('health_check', False, e)
            logger.exception("redis_health_check_error error=%s", e)
            return False

    def set(self, key: str, value: Union[str, bytes], ex: Optional[int] = None, px: Optional[int] = None, nx: bool = False, xx: bool = False) -> bool:
        logger.debug("redis_set_start key=%s ex=%s px=%s nx=%s xx=%s",
                    key, ex, px, nx, xx)
        
        if not self._client:
            logger.error("redis_set_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("redis_set_executing key=%s", key)
            result = self._client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
            
            success = result is True
            logger.info("redis_set_complete key=%s success=%s", key, success)
            
            self._update_metrics('set', success)
            
            if self.event_config.enabled and success:
                self._publish_event('set', {
                    'key': key,
                    'has_expiry': ex is not None or px is not None
                })
            
            return success
            
        except Exception as e:
            self._update_metrics('set', False, e)
            logger.exception("redis_set_error key=%s error=%s", key, e)
            raise

    def get(self, key: str) -> Optional[str]:
        logger.debug("redis_get_start key=%s", key)
        
        if not self._client:
            logger.error("redis_get_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("redis_get_executing key=%s", key)
            result = self._client.get(key)
            
            found = result is not None
            logger.info("redis_get_complete key=%s found=%s", key, found)
            
            self._update_metrics('get', True)
            
            if self.event_config.enabled:
                self._publish_event('get', {
                    'key': key,
                    'found': found
                })
            
            return result
            
        except Exception as e:
            self._update_metrics('get', False, e)
            logger.exception("redis_get_error key=%s error=%s", key, e)
            raise

    def delete(self, *keys: str) -> int:
        logger.debug("redis_delete_start key_count=%s", len(keys))
        
        if not self._client:
            logger.error("redis_delete_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("redis_delete_executing keys=%s", keys)
            count = self._client.delete(*keys)
            
            logger.info("redis_delete_complete deleted=%s", count)
            
            self._update_metrics('delete', True)
            
            if self.event_config.enabled:
                self._publish_event('delete', {
                    'key_count': len(keys),
                    'deleted_count': count
                })
            
            return count
            
        except Exception as e:
            self._update_metrics('delete', False, e)
            logger.exception("redis_delete_error error=%s", e)
            raise

    def exists(self, *keys: str) -> int:
        logger.debug("redis_exists_start key_count=%s", len(keys))
        
        if not self._client:
            logger.error("redis_exists_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("redis_exists_executing keys=%s", keys)
            count = self._client.exists(*keys)
            
            logger.info("redis_exists_complete count=%s", count)
            
            self._update_metrics('exists', True)
            
            return count
            
        except Exception as e:
            self._update_metrics('exists', False, e)
            logger.exception("redis_exists_error error=%s", e)
            raise

    def keys(self, pattern: str = "*") -> List[str]:
        logger.debug("redis_keys_start pattern=%s", pattern)
        
        if not self._client:
            logger.error("redis_keys_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("redis_keys_executing pattern=%s", pattern)
            result = self._client.keys(pattern)
            
            logger.info("redis_keys_complete count=%s", len(result))
            
            self._update_metrics('keys', True)
            
            if self.event_config.enabled:
                self._publish_event('keys', {
                    'pattern': pattern,
                    'count': len(result)
                })
            
            return result
            
        except Exception as e:
            self._update_metrics('keys', False, e)
            logger.exception("redis_keys_error pattern=%s error=%s", pattern, e)
            raise

    def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        logger.debug("redis_hset_start name=%s field_count=%s", name, len(mapping))
        
        if not self._client:
            logger.error("redis_hset_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("redis_hset_executing name=%s", name)
            count = self._client.hset(name, mapping=mapping)
            
            logger.info("redis_hset_complete name=%s count=%s", name, count)
            
            self._update_metrics('hset', True)
            
            if self.event_config.enabled:
                self._publish_event('hset', {
                    'name': name,
                    'field_count': len(mapping)
                })
            
            return count
            
        except Exception as e:
            self._update_metrics('hset', False, e)
            logger.exception("redis_hset_error name=%s error=%s", name, e)
            raise

    def hget(self, name: str, key: str) -> Optional[str]:
        logger.debug("redis_hget_start name=%s key=%s", name, key)
        
        if not self._client:
            logger.error("redis_hget_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("redis_hget_executing name=%s key=%s", name, key)
            result = self._client.hget(name, key)
            
            found = result is not None
            logger.info("redis_hget_complete name=%s key=%s found=%s", name, key, found)
            
            self._update_metrics('hget', True)
            
            return result
            
        except Exception as e:
            self._update_metrics('hget', False, e)
            logger.exception("redis_hget_error name=%s key=%s error=%s", name, key, e)
            raise

    def hgetall(self, name: str) -> Dict[str, str]:
        logger.debug("redis_hgetall_start name=%s", name)
        
        if not self._client:
            logger.error("redis_hgetall_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("redis_hgetall_executing name=%s", name)
            result = self._client.hgetall(name)
            
            logger.info("redis_hgetall_complete name=%s field_count=%s", name, len(result))
            
            self._update_metrics('hgetall', True)
            
            if self.event_config.enabled:
                self._publish_event('hgetall', {
                    'name': name,
                    'field_count': len(result)
                })
            
            return result
            
        except Exception as e:
            self._update_metrics('hgetall', False, e)
            logger.exception("redis_hgetall_error name=%s error=%s", name, e)
            raise

    def lpush(self, name: str, *values: str) -> int:
        logger.debug("redis_lpush_start name=%s value_count=%s", name, len(values))
        
        if not self._client:
            logger.error("redis_lpush_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("redis_lpush_executing name=%s", name)
            count = self._client.lpush(name, *values)
            
            logger.info("redis_lpush_complete name=%s count=%s", name, count)
            
            self._update_metrics('lpush', True)
            
            if self.event_config.enabled:
                self._publish_event('lpush', {
                    'name': name,
                    'value_count': len(values),
                    'new_length': count
                })
            
            return count
            
        except Exception as e:
            self._update_metrics('lpush', False, e)
            logger.exception("redis_lpush_error name=%s error=%s", name, e)
            raise

    def rpush(self, name: str, *values: str) -> int:
        logger.debug("redis_rpush_start name=%s value_count=%s", name, len(values))
        
        if not self._client:
            logger.error("redis_rpush_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("redis_rpush_executing name=%s", name)
            count = self._client.rpush(name, *values)
            
            logger.info("redis_rpush_complete name=%s count=%s", name, count)
            
            self._update_metrics('rpush', True)
            
            if self.event_config.enabled:
                self._publish_event('rpush', {
                    'name': name,
                    'value_count': len(values),
                    'new_length': count
                })
            
            return count
            
        except Exception as e:
            self._update_metrics('rpush', False, e)
            logger.exception("redis_rpush_error name=%s error=%s", name, e)
            raise

    def lrange(self, name: str, start: int, end: int) -> List[str]:
        logger.debug("redis_lrange_start name=%s start=%s end=%s", name, start, end)
        
        if not self._client:
            logger.error("redis_lrange_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("redis_lrange_executing name=%s", name)
            result = self._client.lrange(name, start, end)
            
            logger.info("redis_lrange_complete name=%s count=%s", name, len(result))
            
            self._update_metrics('lrange', True)
            
            return result
            
        except Exception as e:
            self._update_metrics('lrange', False, e)
            logger.exception("redis_lrange_error name=%s error=%s", name, e)
            raise

    def incr(self, key: str, amount: int = 1) -> int:
        logger.debug("redis_incr_start key=%s amount=%s", key, amount)
        
        if not self._client:
            logger.error("redis_incr_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("redis_incr_executing key=%s", key)
            result = self._client.incr(key, amount)
            
            logger.info("redis_incr_complete key=%s new_value=%s", key, result)
            
            self._update_metrics('incr', True)
            
            if self.event_config.enabled:
                self._publish_event('incr', {
                    'key': key,
                    'amount': amount,
                    'new_value': result
                })
            
            return result
            
        except Exception as e:
            self._update_metrics('incr', False, e)
            logger.exception("redis_incr_error key=%s error=%s", key, e)
            raise

    def decr(self, key: str, amount: int = 1) -> int:
        logger.debug("redis_decr_start key=%s amount=%s", key, amount)
        
        if not self._client:
            logger.error("redis_decr_not_connected")
            raise RuntimeError("Client not connected")
        
        try:
            self._check_rate_limit()
            
            logger.debug("redis_decr_executing key=%s", key)
            result = self._client.decr(key, amount)
            
            logger.info("redis_decr_complete key=%s new_value=%s", key, result)
            
            self._update_metrics('decr', True)
            
            if self.event_config.enabled:
                self._publish_event('decr', {
                    'key': key,
                    'amount': amount,
                    'new_value': result
                })
            
            return result
            
        except Exception as e:
            self._update_metrics('decr', False, e)
            logger.exception("redis_decr_error key=%s error=%s", key, e)
            raise