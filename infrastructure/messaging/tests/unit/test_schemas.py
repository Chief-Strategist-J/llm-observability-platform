import pytest
from pydantic import ValidationError
from domain.models.schemas import (
    KafkaEventSchema,
    ConsumerOffsetSchema,
    EventQueryParams,
    DatabaseConfig,
    ProcessingConfig,
    AvroSchema,
    ProtobufSchema,
    JsonSchemaDefinition,
    SchemaRegistryConfig,
)


class TestKafkaEventSchema:
    def test_valid_schema(self):
        schema = KafkaEventSchema(
            topic="test-topic",
            partition=0,
            offset=1,
            key="test-key",
            value='{"data": "test"}',
            timestamp=1234567890
        )
        assert schema.topic == "test-topic"
        assert schema.partition == 0

    def test_invalid_partition(self):
        with pytest.raises(ValidationError):
            KafkaEventSchema(
                topic="test-topic",
                partition=-1,
                offset=1,
                key="test-key",
                value='{"data": "test"}',
                timestamp=1234567890
            )


class TestConsumerOffsetSchema:
    def test_valid_schema(self):
        schema = ConsumerOffsetSchema(
            consumer_group="test-group",
            topic="test-topic",
            partition=0,
            offset=100
        )
        assert schema.consumer_group == "test-group"
        assert schema.offset == 100


class TestEventQueryParams:
    def test_valid_params(self):
        params = EventQueryParams(
            topic="test-topic",
            partition=0,
            limit=50
        )
        assert params.topic == "test-topic"
        assert params.limit == 50

    def test_default_limit(self):
        params = EventQueryParams(topic="test-topic")
        assert params.limit == 100


class TestDatabaseConfig:
    def test_postgresql_config(self):
        config = DatabaseConfig(
            database_type="postgresql",
            connection_string="postgresql://user:pass@localhost:5432/db"
        )
        assert config.database_type == "postgresql"
        assert config.min_connections == 2
        assert config.max_connections == 10

    def test_mongodb_config(self):
        config = DatabaseConfig(
            database_type="mongodb",
            connection_string="mongodb://localhost:27017/",
            database_name="test_db"
        )
        assert config.database_type == "mongodb"
        assert config.database_name == "test_db"

    def test_invalid_database_type(self):
        config = DatabaseConfig(
            database_type="invalid",
            connection_string="test"
        )
        assert config.database_type == "invalid"


class TestProcessingConfig:
    def test_valid_config(self):
        config = ProcessingConfig(
            batch_size=100,
            max_retries=3,
            auto_commit=True
        )
        assert config.batch_size == 100
        assert config.max_retries == 3

    def test_default_values(self):
        config = ProcessingConfig()
        assert config.batch_size == 100
        assert config.max_retries == 3
        assert config.auto_commit is True


class TestAvroSchema:
    def test_valid_avro_schema(self):
        schema = AvroSchema(
            type="record",
            name="TestRecord",
            namespace="com.example",
            fields=[{"name": "id", "type": "int"}],
            doc="Test schema"
        )
        assert schema.type == "record"
        assert schema.name == "TestRecord"
        assert schema.namespace == "com.example"
        assert len(schema.fields) == 1

    def test_avro_schema_without_namespace(self):
        schema = AvroSchema(
            type="record",
            name="TestRecord",
            fields=[{"name": "id", "type": "int"}]
        )
        assert schema.namespace is None


class TestProtobufSchema:
    def test_valid_protobuf_schema(self):
        schema = ProtobufSchema(
            package="com.example",
            syntax="proto3",
            message_name="TestMessage",
            fields=[{"name": "id", "type": "int32"}]
        )
        assert schema.package == "com.example"
        assert schema.syntax == "proto3"
        assert schema.message_name == "TestMessage"

    def test_protobuf_schema_default_syntax(self):
        schema = ProtobufSchema(
            package="com.example",
            message_name="TestMessage",
            fields=[{"name": "id", "type": "int32"}]
        )
        assert schema.syntax == "proto3"


class TestJsonSchemaDefinition:
    def test_valid_json_schema(self):
        schema = JsonSchemaDefinition(
            type="object",
            properties={"name": {"type": "string"}},
            required=["name"],
            title="TestSchema",
            description="Test schema definition"
        )
        assert schema.type == "object"
        assert "name" in schema.properties
        assert "name" in schema.required
        assert schema.title == "TestSchema"

    def test_json_schema_defaults(self):
        schema = JsonSchemaDefinition(
            type="object",
            properties={"name": {"type": "string"}}
        )
        assert schema.schema_version == "http://json-schema.org/draft-07/schema#"
        assert schema.required == []
        assert schema.title is None


class TestSchemaRegistryConfig:
    def test_valid_config(self):
        config = SchemaRegistryConfig(
            url="http://localhost:8081",
            auth={"username": "user", "password": "pass"},
            compatibility="BACKWARD"
        )
        assert config.url == "http://localhost:8081"
        assert config.auth == {"username": "user", "password": "pass"}
        assert config.compatibility == "BACKWARD"

    def test_config_defaults(self):
        config = SchemaRegistryConfig(url="http://localhost:8081")
        assert config.compatibility == "BACKWARD"
        assert config.timeout_ms == 30000

    def test_invalid_timeout(self):
        with pytest.raises(ValidationError):
            SchemaRegistryConfig(
                url="http://localhost:8081",
                timeout_ms=500
            )
