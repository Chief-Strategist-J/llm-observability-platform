def __getattr__(name):
    if name == "PostgresDatabaseAdapter":
        from .postgres_database_adapter import PostgresDatabaseAdapter
        return PostgresDatabaseAdapter
    elif name == "MongoDatabaseAdapter":
        from .mongodb_database_adapter import MongoDatabaseAdapter
        return MongoDatabaseAdapter
    elif name == "ConfluentSchemaRegistryAdapter":
        try:
            from .confluent_schema_registry_adapter import ConfluentSchemaRegistryAdapter
            return ConfluentSchemaRegistryAdapter
        except (ImportError, AttributeError) as e:
            raise ImportError(f"ConfluentSchemaRegistryAdapter requires confluent-kafka with compatible dependencies: {e}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "PostgresDatabaseAdapter",
    "MongoDatabaseAdapter",
    "ConfluentSchemaRegistryAdapter",
]
