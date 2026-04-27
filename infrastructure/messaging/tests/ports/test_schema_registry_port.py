import pytest
from domain.ports.schema_registry_port import SchemaRegistryPort, SchemaInfo, SchemaType


class TestSchemaType:
    def test_schema_type_values(self):
        assert SchemaType.AVRO == "AVRO"
        assert SchemaType.PROTOBUF == "PROTOBUF"
        assert SchemaType.JSON == "JSON"


class TestSchemaInfo:
    def test_schema_info_creation(self):
        schema_info = SchemaInfo(
            subject="test-subject",
            schema_id=1,
            schema_type=SchemaType.AVRO,
            schema='{"type":"record","name":"Test","fields":[]}',
            version=1,
            compatibility="BACKWARD"
        )
        assert schema_info.subject == "test-subject"
        assert schema_info.schema_id == 1
        assert schema_info.schema_type == SchemaType.AVRO
        assert schema_info.version == 1
        assert schema_info.compatibility == "BACKWARD"

    def test_schema_info_optional_fields(self):
        schema_info = SchemaInfo(
            subject="test-subject",
            schema_id=1,
            schema_type=SchemaType.JSON,
            schema='{"type":"object"}',
            version=1
        )
        assert schema_info.compatibility is None


class TestSchemaRegistryPort:
    def test_port_is_abstract(self):
        with pytest.raises(TypeError):
            SchemaRegistryPort()


class MockSchemaRegistryPort(SchemaRegistryPort):
    def register_schema(self, subject: str, schema: str, schema_type: SchemaType) -> int:
        return 1

    def get_schema(self, schema_id: int) -> SchemaInfo:
        return SchemaInfo(
            subject="test",
            schema_id=schema_id,
            schema_type=SchemaType.AVRO,
            schema='{"type":"record"}',
            version=1
        )

    def get_schema_by_subject(self, subject: str, version: int = None) -> SchemaInfo:
        return SchemaInfo(
            subject=subject,
            schema_id=1,
            schema_type=SchemaType.AVRO,
            schema='{"type":"record"}',
            version=1
        )

    def get_latest_schema(self, subject: str) -> SchemaInfo:
        return SchemaInfo(
            subject=subject,
            schema_id=1,
            schema_type=SchemaType.AVRO,
            schema='{"type":"record"}',
            version=1
        )

    def list_subjects(self) -> list:
        return ["subject1", "subject2"]

    def list_versions(self, subject: str) -> list:
        return [1, 2, 3]

    def check_compatibility(self, subject: str, schema: str, schema_type: SchemaType) -> bool:
        return True

    def update_compatibility(self, subject: str, compatibility: str) -> bool:
        return True

    def delete_subject(self, subject: str) -> bool:
        return True

    def serialize(self, subject: str, data: dict, schema_id: int = None) -> bytes:
        return b"serialized"

    def deserialize(self, data: bytes, schema_id: int = None) -> dict:
        return {"data": "test"}

    def close(self):
        pass


class TestMockSchemaRegistryPort:
    @pytest.fixture
    def mock_registry(self):
        return MockSchemaRegistryPort()

    def test_register_schema(self, mock_registry):
        schema_id = mock_registry.register_schema("test-subject", '{"type":"record"}', SchemaType.AVRO)
        assert schema_id == 1

    def test_get_schema(self, mock_registry):
        schema = mock_registry.get_schema(1)
        assert schema.schema_id == 1
        assert schema.subject == "test"

    def test_get_schema_by_subject(self, mock_registry):
        schema = mock_registry.get_schema_by_subject("test-subject")
        assert schema.subject == "test-subject"

    def test_list_subjects(self, mock_registry):
        subjects = mock_registry.list_subjects()
        assert subjects == ["subject1", "subject2"]

    def test_list_versions(self, mock_registry):
        versions = mock_registry.list_versions("test-subject")
        assert versions == [1, 2, 3]

    def test_check_compatibility(self, mock_registry):
        is_compatible = mock_registry.check_compatibility("test-subject", '{"type":"record"}', SchemaType.AVRO)
        assert is_compatible is True

    def test_update_compatibility(self, mock_registry):
        result = mock_registry.update_compatibility("test-subject", "BACKWARD")
        assert result is True

    def test_delete_subject(self, mock_registry):
        result = mock_registry.delete_subject("test-subject")
        assert result is True

    def test_serialize(self, mock_registry):
        serialized = mock_registry.serialize("test-subject", {"data": "test"})
        assert serialized == b"serialized"

    def test_deserialize(self, mock_registry):
        deserialized = mock_registry.deserialize(b"serialized", 1)
        assert deserialized == {"data": "test"}

    def test_close(self, mock_registry):
        mock_registry.close()
