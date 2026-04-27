import pytest
from unittest.mock import Mock, MagicMock
from domain.services.schema_aware_event_handler import SchemaAwareEventHandler
from domain.ports.database_port import EventRecord, ConsumerOffset
from domain.ports.schema_registry_port import SchemaType
from domain.services.event_handler import ConsumerRecord


class TestSchemaAwareEventHandler:
    @pytest.fixture
    def mock_database(self):
        db = Mock()
        db.save_event.return_value = "event-id-123"
        return db

    @pytest.fixture
    def mock_schema_registry(self):
        registry = Mock()
        registry.register_schema.return_value = 1
        registry.serialize.return_value = b"serialized"
        registry.check_compatibility.return_value = True
        return registry

    @pytest.fixture
    def handler(self, mock_database, mock_schema_registry):
        return SchemaAwareEventHandler(database=mock_database, schema_registry=mock_schema_registry)

    @pytest.fixture
    def sample_record(self):
        return ConsumerRecord(
            topic="test-topic",
            partition=0,
            offset=1,
            key="test-key",
            value={"data": "test"},
            timestamp=1234567890
        )

    def test_initialization(self, handler, mock_database, mock_schema_registry):
        assert handler._database == mock_database
        assert handler._schema_registry == mock_schema_registry
        assert handler._subject_mapping == {}

    def test_register_subject_mapping(self, handler):
        handler.register_subject_mapping("test-topic", "test-subject")
        assert handler._subject_mapping["test-topic"] == "test-subject"

    def test_register_schema(self, handler, mock_schema_registry):
        schema_id = handler.register_schema("test-subject", '{"type":"record"}', SchemaType.AVRO)
        assert schema_id == 1
        mock_schema_registry.register_schema.assert_called_once()

    def test_get_schema(self, handler, mock_schema_registry):
        mock_schema = MagicMock()
        mock_schema_registry.get_schema_by_subject.return_value = mock_schema
        result = handler.get_schema("test-subject")
        assert result == mock_schema
        mock_schema_registry.get_schema_by_subject.assert_called_once()

    def test_check_schema_compatibility(self, handler, mock_schema_registry):
        result = handler.check_schema_compatibility("test-subject", '{"type":"record"}', SchemaType.AVRO)
        assert result is True
        mock_schema_registry.check_compatibility.assert_called_once()

    def test_list_registered_subjects(self, handler, mock_schema_registry):
        mock_schema_registry.list_subjects.return_value = ["subject1", "subject2"]
        result = handler.list_registered_subjects()
        assert result == ["subject1", "subject2"]
        mock_schema_registry.list_subjects.assert_called_once()

    def test_serialize_and_produce(self, handler, mock_schema_registry):
        handler.register_subject_mapping("test-topic", "test-subject")
        result = handler.serialize_and_produce("test-topic", {"data": "test"})
        assert result == b"serialized"
        mock_schema_registry.serialize.assert_called_once()

    def test_serialize_and_produce_no_mapping(self, handler):
        result = handler.serialize_and_produce("test-topic", {"data": "test"})
        assert result == b"{'data': 'test'}"

    def test_list_registered_subjects(self, handler, mock_schema_registry):
        mock_schema_registry.list_subjects.return_value = ["subject1", "subject2"]
        subjects = handler.list_registered_subjects()
        assert subjects == ["subject1", "subject2"]
        mock_schema_registry.list_subjects.assert_called_once()

    def test_close(self, handler, mock_database, mock_schema_registry):
        handler.close()
        mock_database.close.assert_called_once()
        mock_schema_registry.close.assert_called_once()
