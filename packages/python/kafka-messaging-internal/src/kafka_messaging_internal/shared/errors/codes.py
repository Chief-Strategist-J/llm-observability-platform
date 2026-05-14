"""Error code definitions and factory functions."""

from typing import Optional, Dict, Any
from .exceptions import ValidationError, BusinessError, DatabaseError, SchemaRegistryError, KafkaError, TimeoutError, ConfigurationError, DependencyInjectionError


def validation_failed(message: str, code: Optional[str] = None, field: Optional[str] = None, value: Optional[Any] = None) -> ValidationError:
    """Create a validation error with proper error code."""
    return ValidationError(
        message=message,
        field=field,
        value=value
    )


def business_error(message: str, code: Optional[str] = None, business_rule: Optional[str] = None) -> BusinessError:
    """Create a business error with proper error code."""
    return BusinessError(
        message=message,
        business_rule=business_rule
    )


def database_error(message: str, code: Optional[str] = None, operation: Optional[str] = None, table: Optional[str] = None) -> DatabaseError:
    """Create a database error with proper error code."""
    return DatabaseError(
        message=message,
        operation=operation,
        table=table
    )


def schema_registry_error(message: str, code: Optional[str] = None, schema_id: Optional[str] = None, subject: Optional[str] = None) -> SchemaRegistryError:
    """Create a schema registry error with proper error code."""
    return SchemaRegistryError(
        message=message,
        schema_id=schema_id,
        subject=subject
    )


def kafka_error(message: str, code: Optional[str] = None, topic: Optional[str] = None, partition: Optional[int] = None) -> KafkaError:
    """Create a Kafka error with proper error code."""
    return KafkaError(
        message=message,
        topic=topic,
        partition=partition
    )


def timeout_error(message: str, code: Optional[str] = None, operation: Optional[str] = None, timeout_seconds: Optional[float] = None) -> TimeoutError:
    """Create a timeout error with proper error code."""
    return TimeoutError(
        message=message,
        operation=operation,
        timeout_seconds=timeout_seconds
    )


def configuration_error(message: str, code: Optional[str] = None, config_key: Optional[str] = None) -> ConfigurationError:
    """Create a configuration error with proper error code."""
    return ConfigurationError(
        message=message,
        config_key=config_key
    )


def dependency_injection_error(message: str, code: Optional[str] = None, service_type: Optional[str] = None) -> DependencyInjectionError:
    """Create a dependency injection error with proper error code."""
    return DependencyInjectionError(
        message=message,
        service_type=service_type
    )
