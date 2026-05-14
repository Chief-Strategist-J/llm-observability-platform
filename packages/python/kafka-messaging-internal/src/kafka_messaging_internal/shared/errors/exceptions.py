"""Custom exceptions for the Kafka messaging internal package."""

from typing import Optional, Any, Dict


class BaseError(Exception):
    """Base exception class for all custom exceptions."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None, http_status: int = 500):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.http_status = http_status
        self.code = error_code or "UNKNOWN_ERROR"


class ValidationError(BaseError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, 
                 value: Optional[Any] = None):
        super().__init__(message, "VALIDATION_ERROR", http_status=400)
        self.field = field
        self.value = value


class BusinessError(BaseError):
    """Raised when business logic validation fails."""
    
    def __init__(self, message: str, business_rule: Optional[str] = None):
        super().__init__(message, "BUSINESS_ERROR", http_status=422)
        self.business_rule = business_rule


class DatabaseError(BaseError):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, operation: Optional[str] = None, 
                 table: Optional[str] = None):
        super().__init__(message, "DATABASE_ERROR", http_status=500)
        self.operation = operation
        self.table = table


class SchemaRegistryError(BaseError):
    """Raised when schema registry operations fail."""
    
    def __init__(self, message: str, schema_id: Optional[str] = None, 
                 subject: Optional[str] = None):
        super().__init__(message, "SCHEMA_REGISTRY_ERROR", http_status=500)
        self.schema_id = schema_id
        self.subject = subject


class ConfigurationError(BaseError):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message, "CONFIGURATION_ERROR")
        self.config_key = config_key


class DependencyInjectionError(BaseError):
    """Raised when dependency injection fails."""
    
    def __init__(self, message: str, service_type: Optional[str] = None):
        super().__init__(message, "DEPENDENCY_INJECTION_ERROR")
        self.service_type = service_type


class KafkaError(BaseError):
    """Raised when Kafka operations fail."""
    
    def __init__(self, message: str, topic: Optional[str] = None, 
                 partition: Optional[int] = None):
        super().__init__(message, "KAFKA_ERROR")
        self.topic = topic
        self.partition = partition


class TimeoutError(BaseError):
    """Raised when operations timeout."""
    
    def __init__(self, message: str, operation: Optional[str] = None, 
                 timeout_seconds: Optional[float] = None):
        super().__init__(message, "TIMEOUT_ERROR")
        self.operation = operation
        self.timeout_seconds = timeout_seconds


def map_adapter_error(adapter_type: str, operation: str, original_error: Exception) -> BaseError:
    """Map adapter errors to appropriate exception types with tracing context."""
    error_message = f"{adapter_type} adapter failed during {operation}: {str(original_error)}"
    error_str = str(original_error).lower()
    
    # Map based on adapter type and error patterns
    if adapter_type == 'database':
        if 'connection' in error_str or 'timeout' in error_str:
            return DatabaseError(error_message, operation=operation)
        elif 'constraint' in error_str or 'duplicate' in error_str:
            return DatabaseError(
                error_message, 
                operation=operation, 
                http_status=409
            )
        elif 'not found' in error_str or 'no rows' in error_str:
            return DatabaseError(
                error_message, 
                operation=operation, 
                http_status=404
            )
        else:
            return DatabaseError(error_message, operation=operation)
    
    elif adapter_type == 'schema_registry':
        if '404' in error_str:
            return SchemaRegistryError(
                error_message, 
                http_status=404
            )
        elif '409' in error_str or 'conflict' in error_str:
            return SchemaRegistryError(
                error_message, 
                http_status=409
            )
        elif 'connection' in error_str or 'timeout' in error_str:
            return SchemaRegistryError(error_message, http_status=503)
        else:
            return SchemaRegistryError(error_message)
    
    elif adapter_type == 'kafka':
        return KafkaError(error_message)
    else:
        return BaseError(error_message, error_code="ADAPTER_ERROR")
