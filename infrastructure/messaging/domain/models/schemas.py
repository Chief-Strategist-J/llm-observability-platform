from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Dict, Optional, List
from datetime import datetime
from enum import Enum


class EventStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class EventType(str, Enum):
    MESSAGE = "message"
    METADATA = "metadata"
    CONTROL = "control"


class KafkaEventSchema(BaseModel):
    model_config = ConfigDict(extra='allow')

    topic: str = Field(..., description="Kafka topic name")
    partition: int = Field(..., ge=0, description="Partition number")
    offset: int = Field(..., ge=0, description="Message offset")
    key: Optional[str] = Field(None, description="Message key")
    value: Any = Field(..., description="Message value (can be any JSON-serializable type)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    headers: Optional[Dict[str, Any]] = Field(None, description="Message headers")
    event_type: EventType = Field(default=EventType.MESSAGE, description="Type of event")
    status: EventStatus = Field(default=EventStatus.PENDING, description="Processing status")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    retry_count: int = Field(default=0, ge=0, description="Number of retry attempts")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Record update timestamp")


class ConsumerOffsetSchema(BaseModel):
    model_config = ConfigDict(extra='allow')

    consumer_group: str = Field(..., description="Consumer group ID")
    topic: str = Field(..., description="Kafka topic name")
    partition: int = Field(..., ge=0, description="Partition number")
    offset: int = Field(..., ge=0, description="Committed offset")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class BatchProcessingResult(BaseModel):
    model_config = ConfigDict(extra='allow')

    total_events: int = Field(..., description="Total number of events processed")
    successful: int = Field(..., description="Number of successfully processed events")
    failed: int = Field(..., description="Number of failed events")
    event_ids: List[str] = Field(default_factory=list, description="List of event IDs")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of errors with event IDs")
    processing_time_ms: int = Field(..., description="Total processing time in milliseconds")


class EventQueryParams(BaseModel):
    model_config = ConfigDict(extra='allow')

    topic: Optional[str] = Field(None, description="Filter by topic")
    partition: Optional[int] = Field(None, ge=0, description="Filter by partition")
    status: Optional[EventStatus] = Field(None, description="Filter by status")
    event_type: Optional[EventType] = Field(None, description="Filter by event type")
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


class DatabaseConfig(BaseModel):
    model_config = ConfigDict(extra='allow')

    database_type: str = Field(..., description="Database type: postgresql or mongodb")
    connection_string: str = Field(..., description="Database connection string")
    database_name: Optional[str] = Field(None, description="Database name (for MongoDB)")
    min_connections: int = Field(default=2, ge=1, description="Minimum connection pool size")
    max_connections: int = Field(default=10, ge=1, description="Maximum connection pool size")


class ProcessingConfig(BaseModel):
    model_config = ConfigDict(extra='allow')

    batch_size: int = Field(default=100, ge=1, le=1000, description="Batch processing size")
    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts")
    retry_delay_ms: int = Field(default=1000, ge=0, description="Retry delay in milliseconds")
    auto_commit: bool = Field(default=True, description="Auto-commit processed events")
    cleanup_days: int = Field(default=30, ge=0, description="Days to keep old events")


class AvroSchema(BaseModel):
    model_config = ConfigDict(extra='allow')

    type: str = Field(..., description="Avro type definition")
    name: str = Field(..., description="Record name")
    namespace: Optional[str] = Field(None, description="Schema namespace")
    fields: List[Dict[str, Any]] = Field(..., description="Field definitions")
    doc: Optional[str] = Field(None, description="Schema documentation")


class ProtobufSchema(BaseModel):
    model_config = ConfigDict(extra='allow')

    package: str = Field(..., description="Protobuf package name")
    syntax: str = Field(default="proto3", description="Protobuf syntax version")
    message_name: str = Field(..., description="Message name")
    fields: List[Dict[str, Any]] = Field(..., description="Field definitions")
    options: Optional[Dict[str, str]] = Field(None, description="Protobuf options")


class JsonSchemaDefinition(BaseModel):
    model_config = ConfigDict(extra='allow')

    schema_version: str = Field(default="http://json-schema.org/draft-07/schema#", description="JSON Schema version", alias="$schema")
    type: str = Field(..., description="JSON type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Property definitions")
    required: List[str] = Field(default_factory=list, description="Required fields")
    title: Optional[str] = Field(None, description="Schema title")
    description: Optional[str] = Field(None, description="Schema description")


class SchemaRegistryConfig(BaseModel):
    model_config = ConfigDict(extra='allow')

    url: str = Field(..., description="Schema Registry URL")
    auth: Optional[Dict[str, str]] = Field(None, description="Authentication credentials")
    compatibility: str = Field(default="BACKWARD", description="Default compatibility level")
    timeout_ms: int = Field(default=30000, ge=1000, description="Request timeout in milliseconds")
