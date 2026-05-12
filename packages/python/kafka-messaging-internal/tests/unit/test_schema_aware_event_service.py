"""Unit tests for SchemaAwareEventService."""

import pytest
from unittest.mock import Mock, AsyncMock

from features.schema_aware_events.service import SchemaAwareEventService
from infra.ports.database_port import DatabasePort
from infra.ports.schema_registry_port import SchemaRegistryPort
from shared.types.schema import SchemaType, SchemaInfo


class TestSchemaAwareEventService:
    """Test cases for SchemaAwareEventService"""

    @pytest.fixture
    def mock_database(self):
        """Mock database port"""
        database = Mock(spec=DatabasePort)
        database.save_event = AsyncMock(return_value="test_event_id")
        database.save_events_batch = AsyncMock(return_value=["id1", "id2"])
        database.mark_event_processed = AsyncMock(return_value=True)
        database.get_unprocessed_events = Mock(return_value=[])
        database.save_consumer_offset = AsyncMock(return_value=True)
        database.get_consumer_offset = Mock(return_value=None)
        database.close = Mock()
        return database

    @pytest.fixture
    def mock_schema_registry(self):
        """Mock schema registry port"""
        schema_registry = Mock(spec=SchemaRegistryPort)
        schema_registry.deserialize = Mock(return_value={"deserialized": "data"})
        schema_registry.serialize = Mock(return_value=b"serialized_data")
        schema_registry.register_schema = Mock(return_value=123)
        schema_registry.get_schema_by_subject = Mock(return_value=SchemaInfo(
            subject="test-subject",
            schema_id=123,
            schema_type=SchemaType.JSON,
            schema='{"type": "object"}',
            version=1
        ))
        schema_registry.check_compatibility = Mock(return_value=True)
        schema_registry.update_compatibility = Mock(return_value=True)
        schema_registry.list_subjects = Mock(return_value=["test-subject"])
        schema_registry.close = Mock()
        return schema_registry

    @pytest.fixture
    def event_service(self, mock_database, mock_schema_registry):
        """Create schema-aware event service instance"""
        return SchemaAwareEventService(mock_database, mock_schema_registry)

    def test_init(self, event_service, mock_database, mock_schema_registry):
        """Test service initialization"""
        assert event_service._database == mock_database
        assert event_service._schema_registry == mock_schema_registry
        assert event_service._subject_mapping == {}

    def test_register_subject_mapping(self, event_service):
        """Test registering subject mapping"""
        event_service.register_subject_mapping("test-topic", "test-subject")
        assert event_service._subject_mapping["test-topic"] == "test-subject"

    @pytest.mark.asyncio
    async def test_process_kafka_record_without_deserialization(self, event_service, mock_database):
        """Test processing record without deserialization"""
        record = {
            'topic': 'test-topic',
            'partition': 0,
            'offset': 123,
            'key': 'test-key',
            'value': {'data': 'test'},
            'timestamp': 1640995200000
        }
        
        event_id = await event_service.process_kafka_record(record, deserialize=False)
        
        assert event_id == "test_event_id"
        mock_database.save_event.assert_called_once()
        mock_schema_registry.deserialize.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_kafka_record_with_deserialization(self, event_service, mock_database, mock_schema_registry):
        """Test processing record with deserialization"""
        event_service.register_subject_mapping("test-topic", "test-subject")
        
        record = {
            'topic': 'test-topic',
            'partition': 0,
            'offset': 123,
            'key': 'test-key',
            'value': b'raw_bytes',
            'timestamp': 1640995200000
        }
        
        event_id = await event_service.process_kafka_record(record, deserialize=True)
        
        assert event_id == "test_event_id"
        mock_database.save_event.assert_called_once()
        mock_schema_registry.deserialize.assert_called_once_with(b'raw_bytes')

    @pytest.mark.asyncio
    async def test_process_kafka_records_batch(self, event_service, mock_database):
        """Test processing multiple records"""
        records = [
            {
                'topic': 'test-topic',
                'partition': 0,
                'offset': 123,
                'key': 'key1',
                'value': {'data': 'test1'},
                'timestamp': 1640995200000
            },
            {
                'topic': 'test-topic',
                'partition': 0,
                'offset': 124,
                'key': 'key2',
                'value': {'data': 'test2'},
                'timestamp': 1640995200000
            }
        ]
        
        event_ids = await event_service.process_kafka_records_batch(records, deserialize=False)
        
        assert event_ids == ["id1", "id2"]
        assert mock_database.save_event.call_count == 2

    def test_serialize_and_produce_with_mapping(self, event_service, mock_schema_registry):
        """Test serializing data with subject mapping"""
        event_service.register_subject_mapping("test-topic", "test-subject")
        
        result = event_service.serialize_and_produce("test-topic", {"data": "test"})
        
        assert result == b"serialized_data"
        mock_schema_registry.serialize.assert_called_once_with("test-subject", {"data": "test"})

    def test_serialize_and_produce_without_mapping(self, event_service, mock_schema_registry):
        """Test serializing data without subject mapping"""
        result = event_service.serialize_and_produce("test-topic", {"data": "test"})
        
        assert result == b'{"data": "test"}'
        mock_schema_registry.serialize.assert_not_called()

    def test_register_schema(self, event_service, mock_schema_registry):
        """Test registering a schema"""
        result = event_service.register_schema("test-subject", '{"type": "object"}', SchemaType.JSON)
        
        assert result == 123
        mock_schema_registry.register_schema.assert_called_once_with("test-subject", '{"type": "object"}', SchemaType.JSON)

    def test_get_schema(self, event_service, mock_schema_registry):
        """Test getting schema by subject"""
        result = event_service.get_schema("test-subject", 1)
        
        assert result.subject == "test-subject"
        assert result.schema_id == 123
        mock_schema_registry.get_schema_by_subject.assert_called_once_with("test-subject", 1)

    def test_check_schema_compatibility(self, event_service, mock_schema_registry):
        """Test checking schema compatibility"""
        result = event_service.check_schema_compatibility("test-subject", '{"type": "object"}', SchemaType.JSON)
        
        assert result is True
        mock_schema_registry.check_compatibility.assert_called_once_with("test-subject", '{"type": "object"}', SchemaType.JSON)

    def test_list_registered_subjects(self, event_service, mock_schema_registry):
        """Test listing registered subjects"""
        result = event_service.list_registered_subjects()
        
        assert result == ["test-subject"]
        mock_schema_registry.list_subjects.assert_called_once()

    def test_close(self, event_service, mock_database, mock_schema_registry):
        """Test closing the service"""
        event_service.close()
        mock_database.close.assert_called_once()
        mock_schema_registry.close.assert_called_once()
