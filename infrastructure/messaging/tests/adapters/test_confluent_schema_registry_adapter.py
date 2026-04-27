import pytest
from unittest.mock import Mock, MagicMock, patch
from infrastructure.adapters.confluent_schema_registry_adapter import ConfluentSchemaRegistryAdapter
from domain.ports.schema_registry_port import SchemaInfo, SchemaType


class TestConfluentSchemaRegistryAdapter:
    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        return client

    @pytest.fixture
    def adapter(self, mock_client):
        with patch('infrastructure.adapters.confluent_schema_registry_adapter.ConfluentSchemaRegistryClient', return_value=mock_client):
            adapter = ConfluentSchemaRegistryAdapter(url="http://localhost:8081")
            adapter._client = mock_client
            return adapter

    def test_initialization(self, mock_client):
        with patch('infrastructure.adapters.confluent_schema_registry_adapter.ConfluentSchemaRegistryClient', return_value=mock_client):
            adapter = ConfluentSchemaRegistryAdapter(url="http://localhost:8081")
            assert adapter._base_url == "http://localhost:8081"

    def test_initialization_with_auth(self, mock_client):
        with patch('infrastructure.adapters.confluent_schema_registry_adapter.ConfluentSchemaRegistryClient', return_value=mock_client) as mock_constructor:
            adapter = ConfluentSchemaRegistryAdapter(
                url="http://localhost:8081",
                auth={"basic.auth.user.info": "user:password"}
            )
            mock_constructor.assert_called_once()
            call_kwargs = mock_constructor.call_args[1]
            assert "basic.auth.user.info" in call_kwargs

    def test_register_schema_avro(self, adapter, mock_client):
        mock_client.register_schema.return_value = 1
        schema_id = adapter.register_schema("test-subject", '{"type":"record","name":"Test"}', SchemaType.AVRO)
        assert schema_id == 1
        mock_client.register_schema.assert_called_once()

    def test_register_schema_json(self, adapter, mock_client):
        mock_client.register_schema.return_value = 2
        schema_id = adapter.register_schema("test-subject", '{"type":"object"}', SchemaType.JSON)
        assert schema_id == 2
        mock_client.register_schema.assert_called_once()

    def test_get_schema(self, adapter, mock_client):
        mock_schema = MagicMock()
        mock_schema.subject = "test-subject"
        mock_schema.schema_id = 1
        mock_schema.schema_type = "AVRO"
        mock_schema.schema_str = '{"type":"record"}'
        mock_schema.version = 1
        mock_client.get_schema.return_value = mock_schema

        schema_info = adapter.get_schema(1)
        assert schema_info.subject == "test-subject"
        assert schema_info.schema_id == 1
        assert schema_info.schema_type == SchemaType.AVRO

    def test_get_schema_by_subject(self, adapter, mock_client):
        mock_schema = MagicMock()
        mock_schema.subject = "test-subject"
        mock_schema.schema_id = 1
        mock_schema.schema_type = "AVRO"
        mock_schema.schema_str = '{"type":"record"}'
        mock_schema.version = 1
        mock_client.get_latest_version.return_value = mock_schema

        schema_info = adapter.get_schema_by_subject("test-subject")
        assert schema_info.subject == "test-subject"
        mock_client.get_latest_version.assert_called_once()

    def test_get_schema_by_subject_with_version(self, adapter, mock_client):
        mock_schema = MagicMock()
        mock_schema.subject = "test-subject"
        mock_schema.schema_id = 1
        mock_schema.schema_type = "AVRO"
        mock_schema.schema_str = '{"type":"record"}'
        mock_schema.version = 2
        mock_client.get_version.return_value = mock_schema

        schema_info = adapter.get_schema_by_subject("test-subject", version=2)
        assert schema_info.version == 2
        mock_client.get_version.assert_called_once()

    def test_list_subjects(self, adapter, mock_client):
        mock_client.get_subjects.return_value = ["subject1", "subject2"]
        subjects = adapter.list_subjects()
        assert subjects == ["subject1", "subject2"]
        mock_client.get_subjects.assert_called_once()

    def test_list_versions(self, adapter, mock_client):
        mock_client.get_subject_versions.return_value = [1, 2, 3]
        versions = adapter.list_versions("test-subject")
        assert versions == [1, 2, 3]
        mock_client.get_subject_versions.assert_called_once()

    def test_check_compatibility(self, adapter, mock_client):
        mock_client.check_compatibility.return_value = True
        is_compatible = adapter.check_compatibility("test-subject", '{"type":"record"}', SchemaType.AVRO)
        assert is_compatible is True
        mock_client.check_compatibility.assert_called_once()

    def test_update_compatibility(self, adapter, mock_client):
        mock_client.update_compatibility.return_value = True
        result = adapter.update_compatibility("test-subject", "BACKWARD")
        assert result is True
        mock_client.update_compatibility.assert_called_once()

    def test_delete_subject(self, adapter, mock_client):
        mock_client.delete_subject.return_value = None
        result = adapter.delete_subject("test-subject")
        assert result is True
        mock_client.delete_subject.assert_called_once()

    def test_serialize_avro(self, adapter, mock_client):
        mock_schema = MagicMock()
        mock_schema.subject = "test-subject"
        mock_schema.schema_id = 1
        mock_schema.schema_type = "AVRO"
        mock_schema.schema_str = '{"type":"record"}'
        mock_schema.version = 1
        mock_client.get_latest_version.return_value = mock_schema

        with patch('infrastructure.adapters.confluent_schema_registry_adapter.AvroSerializer') as mock_serializer:
            mock_serializer_instance = MagicMock()
            mock_serializer.return_value = mock_serializer_instance
            mock_serializer_instance.return_value = b"serialized"

            result = adapter.serialize("test-subject", {"data": "test"})
            assert result == b"serialized"

    def test_deserialize_avro(self, adapter, mock_client):
        mock_schema = MagicMock()
        mock_schema.subject = "test-subject"
        mock_schema.schema_id = 1
        mock_schema.schema_type = "AVRO"
        mock_schema.schema_str = '{"type":"record"}'
        mock_schema.version = 1
        mock_client.get_schema.return_value = mock_schema

        with patch('infrastructure.adapters.confluent_schema_registry_adapter.AvroDeserializer') as mock_deserializer:
            mock_deserializer_instance = MagicMock()
            mock_deserializer.return_value = mock_deserializer_instance
            mock_deserializer_instance.return_value = {"data": "test"}

            result = adapter.deserialize(b"serialized", 1)
            assert result == {"data": "test"}

    def test_serialize_json(self, adapter, mock_client):
        mock_schema = MagicMock()
        mock_schema.subject = "test-subject"
        mock_schema.schema_id = 1
        mock_schema.schema_type = "JSON"
        mock_schema.schema_str = '{"type":"object"}'
        mock_schema.version = 1
        mock_client.get_latest_version.return_value = mock_schema

        with patch('infrastructure.adapters.confluent_schema_registry_adapter.JsonSchemaSerializer') as mock_serializer:
            mock_serializer_instance = MagicMock()
            mock_serializer.return_value = mock_serializer_instance
            mock_serializer_instance.return_value = b"serialized"

            result = adapter.serialize("test-subject", {"data": "test"}, SchemaType.JSON)
            assert result == b"serialized"

    def test_deserialize_json(self, adapter, mock_client):
        mock_schema = MagicMock()
        mock_schema.subject = "test-subject"
        mock_schema.schema_id = 1
        mock_schema.schema_type = "JSON"
        mock_schema.schema_str = '{"type":"object"}'
        mock_schema.version = 1
        mock_client.get_schema.return_value = mock_schema

        with patch('infrastructure.adapters.confluent_schema_registry_adapter.JsonSchemaDeserializer') as mock_deserializer:
            mock_deserializer_instance = MagicMock()
            mock_deserializer.return_value = mock_deserializer_instance
            mock_deserializer_instance.return_value = {"data": "test"}

            result = adapter.deserialize(b"serialized", 1, SchemaType.JSON)
            assert result == {"data": "test"}

    def test_close(self, adapter, mock_client):
        adapter.close()
