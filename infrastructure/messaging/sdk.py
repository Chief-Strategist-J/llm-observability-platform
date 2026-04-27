from typing import Optional, Dict, Any, Callable
from domain.ports.database_port import DatabasePort
from domain.ports.schema_registry_port import SchemaRegistryPort, SchemaType
from infrastructure.adapters.postgres_database_adapter import PostgresDatabaseAdapter
from infrastructure.adapters.mongodb_database_adapter import MongoDatabaseAdapter
from domain.services.event_handler import EventHandler, ConsumerRecord
from domain.services.schema_aware_event_handler import SchemaAwareEventHandler
from domain.models.schemas import DatabaseConfig, SchemaRegistryConfig

try:
    from infrastructure.adapters.confluent_schema_registry_adapter import ConfluentSchemaRegistryAdapter
    CONFLUENT_AVAILABLE = True
except (ImportError, AttributeError):
    CONFLUENT_AVAILABLE = False


def create_postgres_sdk(dsn: str, schema_registry_url: Optional[str] = None) -> 'MessagingSDK':
    config = DatabaseConfig(
        database_type="postgresql",
        connection_string=dsn
    )
    sdk = MessagingSDK(database_config=config)
    
    if schema_registry_url:
        schema_config = SchemaRegistryConfig(url=schema_registry_url)
        sdk.configure_schema_registry(schema_config)
    
    return sdk


def create_mongodb_sdk(uri: str, database_name: str = "kafka_events", schema_registry_url: Optional[str] = None) -> 'MessagingSDK':
    config = DatabaseConfig(
        database_type="mongodb",
        connection_string=uri,
        database_name=database_name
    )
    sdk = MessagingSDK(database_config=config)
    
    if schema_registry_url:
        schema_config = SchemaRegistryConfig(url=schema_registry_url)
        sdk.configure_schema_registry(schema_config)
    
    return sdk


def create_schema_registry_sdk(url: str, auth: Optional[Dict[str, str]] = None) -> 'MessagingSDK':
    config = SchemaRegistryConfig(url=url, auth=auth)
    return MessagingSDK(schema_registry_config=config)


class MessagingSDK:
    def __init__(
        self,
        database_config: Optional[DatabaseConfig] = None,
        schema_registry_config: Optional[SchemaRegistryConfig] = None
    ):
        self._database: Optional[DatabasePort] = None
        self._schema_registry: Optional[SchemaRegistryPort] = None
        self._event_handler: Optional[EventHandler] = None
        self._schema_aware_handler: Optional[SchemaAwareEventHandler] = None
        
        if database_config:
            self.configure_database(database_config)
        
        if schema_registry_config:
            self.configure_schema_registry(schema_registry_config)
    
    def configure_database(self, config: DatabaseConfig):
        if config.database_type == "postgresql":
            self._database = PostgresDatabaseAdapter(
                dsn=config.connection_string,
                minconn=config.min_connections,
                maxconn=config.max_connections
            )
        elif config.database_type == "mongodb":
            self._database = MongoDatabaseAdapter(
                uri=config.connection_string,
                database_name=config.database_name or "kafka_events"
            )
        else:
            raise ValueError(f"Unsupported database type: {config.database_type}")
        
        self._event_handler = EventHandler(database=self._database)
        if self._schema_registry:
            self._schema_aware_handler = SchemaAwareEventHandler(
                database=self._database,
                schema_registry=self._schema_registry
            )
    
    def configure_schema_registry(self, config: SchemaRegistryConfig):
        if not CONFLUENT_AVAILABLE:
            raise ImportError("Confluent Schema Registry adapter requires confluent-kafka with compatible dependencies")
        self._schema_registry = ConfluentSchemaRegistryAdapter(
            url=config.url,
            auth=config.auth
        )
        if self._database:
            self._schema_aware_handler = SchemaAwareEventHandler(
                database=self._database,
                schema_registry=self._schema_registry
            )
    
    @property
    def database(self) -> DatabasePort:
        if not self._database:
            raise RuntimeError("Database not configured. Call configure_database() first.")
        return self._database
    
    @property
    def schema_registry(self) -> SchemaRegistryPort:
        if not self._schema_registry:
            raise RuntimeError("Schema Registry not configured. Call configure_schema_registry() first.")
        return self._schema_registry
    
    @property
    def event_handler(self) -> EventHandler:
        if not self._event_handler:
            raise RuntimeError("Event handler not available. Configure database first.")
        return self._event_handler
    
    @property
    def schema_aware_handler(self) -> SchemaAwareEventHandler:
        if not self._schema_aware_handler:
            raise RuntimeError("Schema-aware handler not available. Configure both database and schema registry first.")
        return self._schema_aware_handler
    
    def process_event(self, record: ConsumerRecord) -> str:
        return self.event_handler.process_kafka_record(record)
    
    def process_events_batch(self, records: list) -> list:
        return self.event_handler.process_kafka_records_batch(records)
    
    def register_schema(self, subject: str, schema: str, schema_type: SchemaType = SchemaType.AVRO) -> int:
        return self.schema_registry.register_schema(subject, schema, schema_type)
    
    def get_schema(self, subject: str, version: Optional[int] = None):
        return self.schema_registry.get_schema_by_subject(subject, version)
    
    def list_subjects(self) -> list:
        return self.schema_registry.list_subjects()
    
    def close(self):
        if self._database:
            self._database.close()
        if self._schema_registry:
            self._schema_registry.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
