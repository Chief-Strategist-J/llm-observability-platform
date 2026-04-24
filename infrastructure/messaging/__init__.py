def __getattr__(name):
    if name == "MessagingSDK":
        from .sdk import MessagingSDK
        return MessagingSDK
    elif name == "create_postgres_sdk":
        from .sdk import create_postgres_sdk
        return create_postgres_sdk
    elif name == "create_mongodb_sdk":
        from .sdk import create_mongodb_sdk
        return create_mongodb_sdk
    elif name == "create_schema_registry_sdk":
        from .sdk import create_schema_registry_sdk
        return create_schema_registry_sdk
    elif name == "DatabaseConfig":
        from .domain.models.schemas import DatabaseConfig
        return DatabaseConfig
    elif name == "SchemaRegistryConfig":
        from .domain.models.schemas import SchemaRegistryConfig
        return SchemaRegistryConfig
    elif name == "ProcessingConfig":
        from .domain.models.schemas import ProcessingConfig
        return ProcessingConfig
    elif name == "AvroSchema":
        from .domain.models.schemas import AvroSchema
        return AvroSchema
    elif name == "ProtobufSchema":
        from .domain.models.schemas import ProtobufSchema
        return ProtobufSchema
    elif name == "JsonSchemaDefinition":
        from .domain.models.schemas import JsonSchemaDefinition
        return JsonSchemaDefinition
    elif name == "DatabasePort":
        from .domain.ports.database_port import DatabasePort
        return DatabasePort
    elif name == "EventRecord":
        from .domain.ports.database_port import EventRecord
        return EventRecord
    elif name == "ConsumerOffset":
        from .domain.ports.database_port import ConsumerOffset
        return ConsumerOffset
    elif name == "SchemaRegistryPort":
        from .domain.ports.schema_registry_port import SchemaRegistryPort
        return SchemaRegistryPort
    elif name == "SchemaInfo":
        from .domain.ports.schema_registry_port import SchemaInfo
        return SchemaInfo
    elif name == "SchemaType":
        from .domain.ports.schema_registry_port import SchemaType
        return SchemaType
    elif name == "EventHandler":
        from .domain.services.event_handler import EventHandler
        return EventHandler
    elif name == "ConsumerRecord":
        from .domain.services.event_handler import ConsumerRecord
        return ConsumerRecord
    elif name == "SchemaAwareEventHandler":
        from .domain.services.schema_aware_event_handler import SchemaAwareEventHandler
        return SchemaAwareEventHandler
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__version__ = "1.0.0"
__all__ = [
    "MessagingSDK",
    "create_postgres_sdk",
    "create_mongodb_sdk",
    "create_schema_registry_sdk",
    "DatabaseConfig",
    "SchemaRegistryConfig",
    "ProcessingConfig",
    "AvroSchema",
    "ProtobufSchema",
    "JsonSchemaDefinition",
    "DatabasePort",
    "EventRecord",
    "ConsumerOffset",
    "SchemaRegistryPort",
    "SchemaInfo",
    "SchemaType",
    "EventHandler",
    "ConsumerRecord",
    "SchemaAwareEventHandler",
]
