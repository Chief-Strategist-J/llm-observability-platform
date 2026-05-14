"""Shared configuration classes with single responsibility."""

import os
from dataclasses import dataclass
from typing import List, Optional
from opentelemetry import trace

_tracer = trace.get_tracer(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration with single responsibility"""
    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_database: str
    mongo_host: str
    mongo_port: int
    mongo_user: str
    mongo_password: str
    mongo_database: str
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create config from environment variables"""
        with _tracer.start_as_current_span("load_database_config") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "configuration")
            span.set_attribute("api.version", "v1")
            
            try:
                config = cls(
                    postgres_host=os.getenv('POSTGRES_HOST', 'localhost'),
                    postgres_port=int(os.getenv('POSTGRES_PORT', '5432')),
                    postgres_user=os.getenv('POSTGRES_USER', 'postgres'),
                    postgres_password=os.getenv('POSTGRES_PASSWORD', ''),
                    postgres_database=os.getenv('POSTGRES_DATABASE', 'kafka_messaging'),
                    mongo_host=os.getenv('MONGO_HOST', 'localhost'),
                    mongo_port=int(os.getenv('MONGO_PORT', '27017')),
                    mongo_user=os.getenv('MONGO_USER', 'mongoadmin'),
                    mongo_password=os.getenv('MONGO_PASSWORD', ''),
                    mongo_database=os.getenv('MONGO_DATABASE', 'kafka_messaging')
                )
                
                span.set_attribute("config.result", "success")
                return config
            except Exception as e:
                span.record_error(e)
                span.set_attribute("config.result", "failed")
                raise


@dataclass
class RedisConfig:
    """Redis configuration with single responsibility"""
    redis_url: str
    ttl_seconds: int
    
    @classmethod
    def from_env(cls) -> 'RedisConfig':
        """Create config from environment variables"""
        with _tracer.start_as_current_span("load_redis_config") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "configuration")
            span.set_attribute("api.version", "v1")
            
            try:
                config = cls(
                    redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379'),
                    ttl_seconds=int(os.getenv('REDIS_TTL_SECONDS', '3600'))
                )
                
                span.set_attribute("config.result", "success")
                return config
            except Exception as e:
                span.record_error(e)
                span.set_attribute("config.result", "failed")
                raise


@dataclass
class QueueConfig:
    """Queue configuration with single responsibility"""
    max_size: int
    per_shard_limit: int
    
    @classmethod
    def from_env(cls) -> 'QueueConfig':
        """Create config from environment variables"""
        with _tracer.start_as_current_span("load_queue_config") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "configuration")
            span.set_attribute("api.version", "v1")
            
            try:
                config = cls(
                    max_size=int(os.getenv('QUEUE_MAX_SIZE', '10000')),
                    per_shard_limit=int(os.getenv('QUEUE_PER_SHARD_LIMIT', '1000'))
                )
                
                span.set_attribute("config.result", "success")
                return config
            except Exception as e:
                span.record_error(e)
                span.set_attribute("config.result", "failed")
                raise


@dataclass
class KafkaConfig:
    """Kafka configuration with single responsibility"""
    bootstrap_servers: str
    producer_config: Optional[dict] = None
    consumer_config: Optional[dict] = None
    
    @classmethod
    def from_env(cls) -> 'KafkaConfig':
        """Create config from environment variables"""
        with _tracer.start_as_current_span("load_kafka_config") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "configuration")
            span.set_attribute("api.version", "v1")
            
            try:
                config = cls(
                    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
                    producer_config={
                        'acks': os.getenv('KAFKA_PRODUCER_ACKS', 'all'),
                        'retries': int(os.getenv('KAFKA_PRODUCER_RETRIES', '3')),
                        'batch.size': int(os.getenv('KAFKA_PRODUCER_BATCH_SIZE', '16384')),
                        'linger.ms': int(os.getenv('KAFKA_PRODUCER_LINGER_MS', '0')),
                    },
                    consumer_config={
                        'auto.offset.reset': os.getenv('KAFKA_CONSUMER_AUTO_OFFSET_RESET', 'earliest'),
                        'enable.auto.commit': os.getenv('KAFKA_CONSUMER_ENABLE_AUTO_COMMIT', 'false').lower() == 'true',
                        'session.timeout.ms': int(os.getenv('KAFKA_CONSUMER_SESSION_TIMEOUT_MS', '30000')),
                    }
                )
                
                span.set_attribute("config.result", "success")
                return config
            except Exception as e:
                span.record_error(e)
                span.set_attribute("config.result", "failed")
                raise


@dataclass
class SchemaRegistryConfig:
    """Schema Registry configuration with single responsibility"""
    url: str
    auth_username: Optional[str] = None
    auth_password: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'SchemaRegistryConfig':
        """Create config from environment variables"""
        with _tracer.start_as_current_span("load_schema_registry_config") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "configuration")
            span.set_attribute("api.version", "v1")
            
            try:
                config = cls(
                    url=os.getenv('SCHEMA_REGISTRY_URL', 'http://localhost:8081'),
                    auth_username=os.getenv('SCHEMA_REGISTRY_USERNAME'),
                    auth_password=os.getenv('SCHEMA_REGISTRY_PASSWORD')
                )
                
                span.set_attribute("config.result", "success")
                return config
            except Exception as e:
                span.record_error(e)
                span.set_attribute("config.result", "failed")
                raise


@dataclass
class OpenTelemetryConfig:
    """OpenTelemetry configuration with single responsibility"""
    service_name: str
    service_version: str
    deployment_env: str
    host_name: str
    otlp_endpoint: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'OpenTelemetryConfig':
        """Create config from environment variables"""
        with _tracer.start_as_current_span("load_opentelemetry_config") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "configuration")
            span.set_attribute("api.version", "v1")
            
            try:
                config = cls(
                    service_name=os.getenv('OTEL_SERVICE_NAME', 'kafka-messaging-internal'),
                    service_version=os.getenv('OTEL_SERVICE_VERSION', '1.0.0'),
                    deployment_env=os.getenv('DEPLOYMENT_ENV', 'development'),
                    host_name=os.getenv('HOST_NAME', 'localhost'),
                    otlp_endpoint=os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT')
                )
                
                span.set_attribute("config.result", "success")
                return config
            except Exception as e:
                span.record_error(e)
                span.set_attribute("config.result", "failed")
                raise


@dataclass
class AppConfig:
    """Main application configuration with single responsibility"""
    database: DatabaseConfig
    redis: RedisConfig
    queue: QueueConfig
    kafka: KafkaConfig
    schema_registry: SchemaRegistryConfig
    opentelemetry: OpenTelemetryConfig
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Create complete config from environment variables"""
        with _tracer.start_as_current_span("load_app_config") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "configuration")
            span.set_attribute("api.version", "v1")
            
            try:
                config = cls(
                    database=DatabaseConfig.from_env(),
                    redis=RedisConfig.from_env(),
                    queue=QueueConfig.from_env(),
                    kafka=KafkaConfig.from_env(),
                    schema_registry=SchemaRegistryConfig.from_env(),
                    opentelemetry=OpenTelemetryConfig.from_env()
                )
                
                span.set_attribute("config.result", "success")
                return config
            except Exception as e:
                span.record_error(e)
                span.set_attribute("config.result", "failed")
                raise
