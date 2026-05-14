"""Service registration for DI container."""

from opentelemetry import trace
from typing import Type, TypeVar, Dict, Any
import os
from .container import DIContainer, get_container
from ..ports.database_port import DatabasePort
from ..ports.schema_registry_port import SchemaRegistryPort
from ...infra.adapters.postgresql.postgres_adapter import PostgresAdapter
from ...infra.adapters.confluent.schema_registry_adapter import ConfluentSchemaRegistryAdapter

T = TypeVar('T')

tracer = trace.get_tracer(__name__)


def register_production_services() -> DIContainer:
    """Register all production services with DI container."""
    container = get_container()
    
    with tracer.start_as_current_span("service_registration") as span:
        span.set_attributes({
            "service.name": "kafka-messaging-internal",
            "feature.name": "di_registration",
            "deployment.env": container.get_config().database_type
        })
        
        try:
            # Skip if in test environment
            if os.getenv('DEPLOYMENT_ENV') == 'test':
                span.set_attribute("skip_registration", "true")
                return container
                
            # Register database adapter based on configuration
            config = container.get_config()
            if config.database_type.lower() == 'postgresql':
                db_adapter = PostgresAdapter(config)
                container.register_singleton(DatabasePort, db_adapter)
                span.set_attribute("database.adapter", "postgresql")
            else:
                raise ValueError(f"Unsupported database type: {config.database_type}")
            
            # Register schema registry adapter
            schema_adapter = ConfluentSchemaRegistryAdapter(config)
            container.register_singleton(SchemaRegistryPort, schema_adapter)
            span.set_attribute("schema_registry.adapter", "confluent")
            
            span.set_status(trace.Status(trace.StatusCode.OK))
            
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise
    
    return container


def register_test_services(database_port: DatabasePort, schema_registry_port: SchemaRegistryPort) -> DIContainer:
    """Register test services with DI container."""
    container = get_container()
    
    with tracer.start_as_current_span("test_service_registration") as span:
        span.set_attributes({
            "service.name": "kafka-messaging-internal-test",
            "feature.name": "test_di_registration",
            "deployment.env": "test"
        })
        
        try:
            container.register_singleton(DatabasePort, database_port)
            container.register_singleton(SchemaRegistryPort, schema_registry_port)
            
            span.set_status(trace.Status(trace.StatusCode.OK))
            
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise
    
    return container
