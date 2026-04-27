import pytest
from unittest.mock import Mock
from datetime import datetime

from application.api.v1.database_api import (
    DatabaseAPI,
    EventRecordRequest,
    BatchEventRequest,
    ConsumerOffsetRequest
)
from application.api.v1.schema_registry_api import (
    SchemaRegistryAPI,
    SchemaRegisterRequest,
    SchemaCompatibilityRequest
)
from application.api.v1.event_handler_api import (
    EventHandlerAPI,
    ConsumerRecordRequest,
    BatchConsumerRecordRequest
)
from domain.ports.schema_registry_port import SchemaType, SchemaInfo
from domain.ports.database_port import EventRecord


@pytest.fixture
def mock_database():
    db = Mock()
    db.save_event.return_value = "event-id-123"
    db.save_events_batch.side_effect = lambda events: [f"id-{i}" for i in range(len(events))]
    db.get_event.return_value = EventRecord(
        topic="test-topic",
        partition=0,
        offset=1,
        key="key",
        value="value",
        timestamp=datetime.now()
    )
    db.get_events_by_topic.return_value = []
    db.mark_event_processed.return_value = True
    db.save_consumer_offset.return_value = True
    db.get_consumer_offset.return_value = 100
    db.delete_events_by_topic.return_value = 5
    db.get_event_count.return_value = 100
    return db


@pytest.fixture
def mock_schema_registry():
    registry = Mock()
    registry.register_schema.return_value = 1
    registry.get_schema.return_value = SchemaInfo(
        subject="test-subject",
        schema_id=1,
        schema_type=SchemaType.AVRO,
        schema='{"type":"record"}',
        version=1
    )
    registry.get_schema_by_subject.return_value = SchemaInfo(
        subject="test-subject",
        schema_id=1,
        schema_type=SchemaType.AVRO,
        schema='{"type":"record"}',
        version=1
    )
    registry.get_latest_schema.return_value = SchemaInfo(
        subject="test-subject",
        schema_id=1,
        schema_type=SchemaType.AVRO,
        schema='{"type":"record"}',
        version=1
    )
    registry.list_subjects.return_value = ["subject1", "subject2"]
    registry.list_versions.return_value = [1, 2, 3]
    registry.delete_subject.return_value = True
    registry.check_compatibility.return_value = True
    registry.update_compatibility.return_value = True
    registry.serialize.return_value = b"serialized-data"
    registry.deserialize.return_value = {"key": "value"}
    return registry


@pytest.fixture
def mock_event_handler():
    handler = Mock()
    handler.process_kafka_record.return_value = "event-id-123"
    handler.process_kafka_records_batch.side_effect = lambda records: [f"id-{i}" for i in range(len(records))]
    handler.save_consumer_offset.return_value = True
    handler.get_consumer_offset.return_value = 100
    handler.get_events_by_topic.return_value = []
    handler.get_event_count.return_value = 100
    return handler


class TestDatabaseAPIPerformance:
    def test_save_event_latency(self, benchmark, mock_database):
        api = DatabaseAPI(mock_database)
        request = EventRecordRequest(
            topic="test-topic",
            partition=0,
            offset=1,
            value="test-value"
        )
        
        result = benchmark(api.save_event, request)
        assert result.event_id == "event-id-123"

    def test_save_events_batch_latency(self, benchmark, mock_database):
        api = DatabaseAPI(mock_database)
        events = [
            EventRecordRequest(topic="test-topic", partition=0, offset=i, value=f"value-{i}")
            for i in range(10)
        ]
        request = BatchEventRequest(events=events)
        
        result = benchmark(api.save_events_batch, request)
        assert result.count == 10

    def test_get_event_latency(self, benchmark, mock_database):
        api = DatabaseAPI(mock_database)
        
        result = benchmark(api.get_event, "event-id-123")
        assert result.topic == "test-topic"

    def test_save_consumer_offset_latency(self, benchmark, mock_database):
        api = DatabaseAPI(mock_database)
        request = ConsumerOffsetRequest(
            consumer_group="test-group",
            topic="test-topic",
            partition=0,
            offset=100
        )
        
        result = benchmark(api.save_consumer_offset, request)
        assert result["success"] is True


class TestSchemaRegistryAPIPerformance:
    def test_register_schema_latency(self, benchmark, mock_schema_registry):
        api = SchemaRegistryAPI(mock_schema_registry)
        request = SchemaRegisterRequest(
            subject="test-subject",
            schema='{"type":"record"}',
            schema_type=SchemaType.AVRO
        )
        
        result = benchmark(api.register_schema, request)
        assert result.schema_id == 1

    def test_get_schema_latency(self, benchmark, mock_schema_registry):
        api = SchemaRegistryAPI(mock_schema_registry)
        
        result = benchmark(api.get_schema, 1)
        assert result.schema_id == 1

    def test_check_compatibility_latency(self, benchmark, mock_schema_registry):
        api = SchemaRegistryAPI(mock_schema_registry)
        request = SchemaCompatibilityRequest(
            subject="test-subject",
            schema='{"type":"record"}',
            schema_type=SchemaType.AVRO
        )
        
        result = benchmark(api.check_compatibility, request)
        assert result["compatible"] is True


class TestEventHandlerAPIPerformance:
    def test_process_record_latency(self, benchmark, mock_event_handler):
        api = EventHandlerAPI(mock_event_handler)
        request = ConsumerRecordRequest(
            topic="test-topic",
            partition=0,
            offset=1,
            value="test-value",
            timestamp=1234567890
        )
        
        result = benchmark(api.process_record, request)
        assert result.event_id == "event-id-123"

    def test_process_records_batch_latency(self, benchmark, mock_event_handler):
        api = EventHandlerAPI(mock_event_handler)
        records = [
            ConsumerRecordRequest(topic="test-topic", partition=0, offset=i, value=f"value-{i}", timestamp=1234567890)
            for i in range(10)
        ]
        request = BatchConsumerRecordRequest(records=records)
        
        result = benchmark(api.process_records_batch, request)
        assert result.count == 10

    def test_save_consumer_offset_latency(self, benchmark, mock_event_handler):
        api = EventHandlerAPI(mock_event_handler)
        request = ConsumerOffsetRequest(
            consumer_group="test-group",
            topic="test-topic",
            partition=0,
            offset=100
        )
        
        result = benchmark(api.save_consumer_offset, request)
        assert result["success"] is True
