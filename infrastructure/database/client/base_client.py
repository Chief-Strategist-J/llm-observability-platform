import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import hmac
import secrets
import time
from threading import Lock
import json

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    MONGODB = "mongodb"
    NEO4J = "neo4j"
    REDIS = "redis"
    QDRANT = "qdrant"


class SecurityLevel(Enum):
    NONE = "none"
    BASIC = "basic"
    TOKEN = "token"
    CERTIFICATE = "certificate"


@dataclass
class SecurityConfig:
    level: SecurityLevel = SecurityLevel.BASIC
    token: Optional[str] = None
    token_expiry: Optional[int] = None
    cert_path: Optional[str] = None
    key_path: Optional[str] = None
    ca_path: Optional[str] = None
    encryption_key: Optional[str] = None
    api_key_header: str = "X-API-Key"
    token_header: str = "Authorization"
    validate_ssl: bool = True
    timeout: int = 30
    max_retries: int = 3
    retry_backoff: float = 1.5
    rate_limit: Optional[int] = None
    rate_window: int = 60
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        logger.debug("security_config_init level=%s has_token=%s has_cert=%s",
                    self.level.value, self.token is not None, self.cert_path is not None)
        
        if self.level == SecurityLevel.TOKEN and not self.token:
            logger.debug("security_config_generating_token")
            self.token = self._generate_token()
            logger.debug("security_config_token_generated")
        
        if self.encryption_key is None and self.level != SecurityLevel.NONE:
            logger.debug("security_config_generating_encryption_key")
            self.encryption_key = self._generate_encryption_key()
            logger.debug("security_config_encryption_key_generated")
        
        logger.info("security_config_initialized level=%s validate_ssl=%s timeout=%s",
                   self.level.value, self.validate_ssl, self.timeout)

    def _generate_token(self) -> str:
        logger.debug("security_token_generation_start")
        token = secrets.token_urlsafe(32)
        logger.debug("security_token_generated length=%s", len(token))
        return token

    def _generate_encryption_key(self) -> str:
        logger.debug("security_encryption_key_generation_start")
        key = secrets.token_urlsafe(32)
        logger.debug("security_encryption_key_generated length=%s", len(key))
        return key

    def encrypt_value(self, value: str) -> str:
        logger.debug("security_encrypt_start value_length=%s", len(value))
        
        if not self.encryption_key:
            logger.warning("security_encrypt_no_key returning_plaintext=True")
            return value
        
        try:
            key_bytes = self.encryption_key.encode('utf-8')
            value_bytes = value.encode('utf-8')
            signature = hmac.new(key_bytes, value_bytes, hashlib.sha256).hexdigest()
            encrypted = f"{signature}:{value}"
            
            logger.debug("security_encrypt_complete encrypted_length=%s", len(encrypted))
            return encrypted
            
        except Exception as e:
            logger.exception("security_encrypt_error error=%s", e)
            raise

    def decrypt_value(self, encrypted: str) -> str:
        logger.debug("security_decrypt_start encrypted_length=%s", len(encrypted))
        
        if not self.encryption_key:
            logger.warning("security_decrypt_no_key returning_plaintext=True")
            return encrypted
        
        try:
            if ':' not in encrypted:
                logger.debug("security_decrypt_no_signature returning_as_is=True")
                return encrypted
            
            signature, value = encrypted.split(':', 1)
            key_bytes = self.encryption_key.encode('utf-8')
            value_bytes = value.encode('utf-8')
            expected_signature = hmac.new(key_bytes, value_bytes, hashlib.sha256).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                logger.error("security_decrypt_signature_mismatch")
                raise ValueError("Invalid signature")
            
            logger.debug("security_decrypt_complete value_length=%s", len(value))
            return value
            
        except Exception as e:
            logger.exception("security_decrypt_error error=%s", e)
            raise

    def validate_token(self, token: str) -> bool:
        logger.debug("security_validate_token_start token_length=%s", len(token) if token else 0)
        
        if self.level == SecurityLevel.NONE:
            logger.debug("security_validate_token_none_level result=True")
            return True
        
        if not self.token:
            logger.warning("security_validate_token_no_configured_token result=False")
            return False
        
        result = hmac.compare_digest(token, self.token)
        logger.info("security_validate_token_complete result=%s", result)
        return result


@dataclass
class ConnectionConfig:
    db_type: DatabaseType
    host: str = "localhost"
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    auth_database: Optional[str] = None
    security: Optional[SecurityConfig] = None
    pool_size: int = 10
    pool_timeout: int = 30
    connection_timeout: int = 30
    socket_timeout: int = 30
    max_idle_time: int = 600
    retry_writes: bool = True
    retry_reads: bool = True
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        logger.debug("connection_config_init db_type=%s host=%s port=%s",
                    self.db_type.value, self.host, self.port)
        
        if self.port is None:
            default_ports = {
                DatabaseType.MONGODB: 27017,
                DatabaseType.NEO4J: 7687,
                DatabaseType.REDIS: 6379,
                DatabaseType.QDRANT: 6333,
            }
            self.port = default_ports.get(self.db_type)
            logger.debug("connection_config_default_port_set port=%s", self.port)
        
        if self.security is None:
            logger.debug("connection_config_creating_default_security")
            self.security = SecurityConfig()
            logger.debug("connection_config_default_security_created")
        
        logger.info("connection_config_initialized db_type=%s host=%s port=%s pool_size=%s",
                   self.db_type.value, self.host, self.port, self.pool_size)


@dataclass
class EventConfig:
    enabled: bool = False
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_prefix: str = "db_events"
    producer_config: Dict[str, Any] = field(default_factory=dict)
    consumer_config: Dict[str, Any] = field(default_factory=dict)
    batch_size: int = 100
    batch_timeout: float = 1.0
    compression_type: str = "gzip"
    acks: str = "all"
    max_retries: int = 3
    retry_backoff_ms: int = 100
    enable_idempotence: bool = True
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        logger.debug("event_config_init enabled=%s kafka_servers=%s topic_prefix=%s",
                    self.enabled, self.kafka_bootstrap_servers, self.kafka_topic_prefix)
        
        if self.enabled:
            if not self.producer_config:
                logger.debug("event_config_setting_default_producer_config")
                self.producer_config = {
                    'acks': self.acks,
                    'compression_type': self.compression_type,
                    'max_in_flight_requests_per_connection': 5,
                    'enable_idempotence': self.enable_idempotence,
                    'retries': self.max_retries,
                    'retry_backoff_ms': self.retry_backoff_ms,
                }
                logger.debug("event_config_default_producer_config_set")
            
            if not self.consumer_config:
                logger.debug("event_config_setting_default_consumer_config")
                self.consumer_config = {
                    'group_id': f'{self.kafka_topic_prefix}_consumer',
                    'auto_offset_reset': 'earliest',
                    'enable_auto_commit': True,
                    'max_poll_records': self.batch_size,
                }
                logger.debug("event_config_default_consumer_config_set")
        
        logger.info("event_config_initialized enabled=%s batch_size=%s compression=%s",
                   self.enabled, self.batch_size, self.compression_type)


class BaseSecureClient(ABC):
    def __init__(self, config: ConnectionConfig, event_config: Optional[EventConfig] = None):
        logger.debug("base_client_init_start db_type=%s", config.db_type.value)
        
        self.config = config
        self.event_config = event_config or EventConfig()
        self._client = None
        self._event_producer = None
        self._rate_limiter = RateLimiter(
            max_calls=config.security.rate_limit if config.security.rate_limit else 1000,
            time_window=config.security.rate_window
        )
        self._connection_lock = Lock()
        self._metrics = {
            'connections': 0,
            'operations': 0,
            'errors': 0,
            'events_published': 0,
            'last_connection': None,
            'last_error': None,
        }
        
        logger.info("base_client_initialized db_type=%s event_enabled=%s",
                   config.db_type.value, self.event_config.enabled)

    @abstractmethod
    def connect(self):
        raise NotImplementedError

    @abstractmethod
    def disconnect(self):
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> bool:
        raise NotImplementedError

    def _init_event_producer(self):
        logger.debug("event_producer_init_start enabled=%s", self.event_config.enabled)
        
        if not self.event_config.enabled:
            logger.debug("event_producer_disabled")
            return
        
        try:
            from kafka import KafkaProducer
            
            logger.debug("event_producer_creating servers=%s", self.event_config.kafka_bootstrap_servers)
            
            self._event_producer = KafkaProducer(
                bootstrap_servers=self.event_config.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                **self.event_config.producer_config
            )
            
            logger.info("event_producer_initialized servers=%s", self.event_config.kafka_bootstrap_servers)
            
        except Exception as e:
            logger.exception("event_producer_init_error error=%s", e)
            raise

    def _publish_event(self, event_type: str, data: Dict[str, Any]):
        logger.debug("event_publish_start type=%s data_keys=%s enabled=%s",
                    event_type, list(data.keys()), self.event_config.enabled)
        
        if not self.event_config.enabled or not self._event_producer:
            logger.debug("event_publish_skipped enabled=%s producer_exists=%s",
                        self.event_config.enabled, self._event_producer is not None)
            return
        
        try:
            topic = f"{self.event_config.kafka_topic_prefix}_{self.config.db_type.value}_{event_type}"
            
            event = {
                'timestamp': time.time(),
                'db_type': self.config.db_type.value,
                'event_type': event_type,
                'data': data,
                'host': self.config.host,
                'port': self.config.port,
            }
            
            logger.debug("event_publish_sending topic=%s", topic)
            
            future = self._event_producer.send(topic, event)
            future.get(timeout=self.event_config.batch_timeout)
            
            self._metrics['events_published'] += 1
            logger.info("event_published type=%s topic=%s", event_type, topic)
            
        except Exception as e:
            logger.exception("event_publish_error type=%s error=%s", event_type, e)

    def _check_rate_limit(self):
        logger.debug("rate_limit_check_start")
        
        if not self._rate_limiter.allow():
            logger.error("rate_limit_exceeded")
            raise Exception("Rate limit exceeded")
        
        logger.debug("rate_limit_check_passed")

    def _update_metrics(self, operation: str, success: bool, error: Optional[Exception] = None):
        logger.debug("metrics_update operation=%s success=%s", operation, success)
        
        self._metrics['operations'] += 1
        
        if not success:
            self._metrics['errors'] += 1
            self._metrics['last_error'] = {
                'operation': operation,
                'error': str(error) if error else 'Unknown',
                'timestamp': time.time()
            }
            logger.warning("metrics_error_recorded operation=%s error=%s", operation, error)
        
        logger.debug("metrics_updated total_ops=%s total_errors=%s",
                    self._metrics['operations'], self._metrics['errors'])

    def get_metrics(self) -> Dict[str, Any]:
        logger.debug("metrics_get_start")
        metrics_copy = self._metrics.copy()
        logger.debug("metrics_retrieved ops=%s errors=%s events=%s",
                    metrics_copy['operations'], metrics_copy['errors'], metrics_copy['events_published'])
        return metrics_copy

    def __enter__(self):
        logger.debug("context_manager_enter db_type=%s", self.config.db_type.value)
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug("context_manager_exit db_type=%s exc_type=%s",
                    self.config.db_type.value, exc_type)
        self.disconnect()


class RateLimiter:
    def __init__(self, max_calls: int, time_window: int):
        logger.debug("rate_limiter_init max_calls=%s window=%s", max_calls, time_window)
        
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self.lock = Lock()
        
        logger.info("rate_limiter_initialized max_calls=%s window=%s", max_calls, time_window)

    def allow(self) -> bool:
        logger.debug("rate_limiter_check_start")
        
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - self.time_window
            
            logger.debug("rate_limiter_cleanup cutoff_time=%s", cutoff_time)
            self.calls = [call_time for call_time in self.calls if call_time > cutoff_time]
            
            current_calls = len(self.calls)
            logger.debug("rate_limiter_current_calls count=%s max=%s", current_calls, self.max_calls)
            
            if current_calls >= self.max_calls:
                logger.warning("rate_limiter_exceeded current=%s max=%s", current_calls, self.max_calls)
                return False
            
            self.calls.append(current_time)
            logger.debug("rate_limiter_allowed new_count=%s", len(self.calls))
            return True


def create_secure_client(config: ConnectionConfig, event_config: Optional[EventConfig] = None):
    logger.debug("factory_create_client_start db_type=%s", config.db_type.value)
    
    from .mongodb_client import SecureMongoDBClient
    from .neo4j_client import SecureNeo4jClient
    from .redis_client import SecureRedisClient
    from .qdrant_client import SecureQdrantClient
    
    clients = {
        DatabaseType.MONGODB: SecureMongoDBClient,
        DatabaseType.NEO4J: SecureNeo4jClient,
        DatabaseType.REDIS: SecureRedisClient,
        DatabaseType.QDRANT: SecureQdrantClient,
    }
    
    client_class = clients.get(config.db_type)
    
    if not client_class:
        logger.error("factory_unsupported_db_type db_type=%s", config.db_type.value)
        raise ValueError(f"Unsupported database type: {config.db_type.value}")
    
    logger.info("factory_creating_client db_type=%s class=%s", config.db_type.value, client_class.__name__)
    return client_class(config, event_config)