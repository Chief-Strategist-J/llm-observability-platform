import pytest
from unittest.mock import Mock
from fastapi import HTTPException

from application.api.v1.schema_registry_api import (
    SchemaRegistryAPI,
    SchemaRegisterRequest,
    SchemaInfoResponse,
    SchemaCompatibilityRequest,
    CompatibilityUpdateRequest,
    SerializationRequest,
    DeserializationRequest
)
from domain.ports.schema_registry_port import SchemaType, SchemaInfo
from application.api.v1.validators import ValidationError


@pytest.fixture
def mock_schema_registry():
    return Mock()


@pytest.fixture
def schema_registry_api(mock_schema_registry):
    return SchemaRegistryAPI(mock_schema_registry)


class TestSchemaRegisterRequest:
    def test_valid_request(self):
        request = SchemaRegisterRequest(
            subject="test-subject",
            schema='{"type":"record","name":"Test","fields":[]}',
            schema_type=SchemaType.AVRO
        )
        assert request.subject == "test-subject"
        assert request.schema_type == SchemaType.AVRO





class TestSchemaCompatibilityRequest:
    def test_valid_request(self):
        request = SchemaCompatibilityRequest(
            subject="test-subject",
            schema='{"type":"record"}',
            schema_type=SchemaType.AVRO
        )
        assert request.subject == "test-subject"



class TestCompatibilityUpdateRequest:
    def test_valid_request(self):
        request = CompatibilityUpdateRequest(
            subject="test-subject",
            compatibility="BACKWARD"
        )
        assert request.subject == "test-subject"
        assert request.compatibility == "BACKWARD"



class TestSerializationRequest:
    def test_valid_request(self):
        request = SerializationRequest(
            subject="test-subject",
            data={"key": "value"}
        )
        assert request.subject == "test-subject"




class TestDeserializationRequest:
    def test_valid_request(self):
        request = DeserializationRequest(
            data="base64encodeddata",
            schema_id=1
        )
        assert request.data == "base64encodeddata"



class TestSchemaRegistryAPIRegisterSchema:
    def test_register_schema_success(self, schema_registry_api, mock_schema_registry):
        request = SchemaRegisterRequest(
            subject="test-subject",
            schema='{"type":"record"}',
            schema_type=SchemaType.AVRO
        )
        mock_schema_registry.register_schema.return_value = 1
        mock_schema_registry.get_schema.return_value = SchemaInfo(
            subject="test-subject",
            schema_id=1,
            schema_type=SchemaType.AVRO,
            schema='{"type":"record"}',
            version=1
        )
        
        response = schema_registry_api.register_schema(request)
        
        assert response.subject == "test-subject"
        assert response.schema_id == 1
        mock_schema_registry.register_schema.assert_called_once()


    def test_register_schema_database_error_raises_500(self, schema_registry_api, mock_schema_registry):
        request = SchemaRegisterRequest(
            subject="test-subject",
            schema='{"type":"record"}',
            schema_type=SchemaType.AVRO
        )
        mock_schema_registry.register_schema.side_effect = Exception("Registry error")
        
        with pytest.raises(HTTPException) as exc:
            schema_registry_api.register_schema(request)
        
        assert exc.value.status_code == 500

    def test_register_schema_empty_subject_raises_400(self, schema_registry_api):
        request = SchemaRegisterRequest(
            subject="",
            schema='{"type":"record"}',
            schema_type=SchemaType.AVRO
        )
        
        with pytest.raises(HTTPException) as exc:
            schema_registry_api.register_schema(request)
        
        assert exc.value.status_code == 400
        assert "subject" in str(exc.value.detail)


class TestSchemaRegistryAPIGetSchema:
    def test_get_schema_success(self, schema_registry_api, mock_schema_registry):
        mock_schema_registry.get_schema.return_value = SchemaInfo(
            subject="test-subject",
            schema_id=1,
            schema_type=SchemaType.AVRO,
            schema='{"type":"record"}',
            version=1
        )
        
        response = schema_registry_api.get_schema(1)
        
        assert response.schema_id == 1
        assert response.subject == "test-subject"

    def test_get_schema_invalid_id_raises_400(self, schema_registry_api):
        with pytest.raises(HTTPException) as exc:
            schema_registry_api.get_schema(0)
        
        assert exc.value.status_code == 400
        assert "schema_id" in str(exc.value.detail)

    def test_get_schema_not_found_raises_404(self, schema_registry_api, mock_schema_registry):
        mock_schema_registry.get_schema.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            schema_registry_api.get_schema(1)
        
        assert exc.value.status_code == 404

    def test_get_schema_negative_id_raises_400(self, schema_registry_api):
        with pytest.raises(HTTPException) as exc:
            schema_registry_api.get_schema(-1)
        
        assert exc.value.status_code == 400
        assert "schema_id" in str(exc.value.detail)


class TestSchemaRegistryAPIGetSchemaBySubject:
    def test_get_schema_by_subject_success(self, schema_registry_api, mock_schema_registry):
        mock_schema_registry.get_schema_by_subject.return_value = SchemaInfo(
            subject="test-subject",
            schema_id=1,
            schema_type=SchemaType.AVRO,
            schema='{"type":"record"}',
            version=1
        )
        
        response = schema_registry_api.get_schema_by_subject("test-subject")
        
        assert response.subject == "test-subject"
        mock_schema_registry.get_schema_by_subject.assert_called_once()

    def test_get_schema_by_subject_not_found_raises_404(self, schema_registry_api, mock_schema_registry):
        mock_schema_registry.get_schema_by_subject.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            schema_registry_api.get_schema_by_subject("test-subject")
        
        assert exc.value.status_code == 404

    def test_get_schema_by_subject_empty_subject_raises_400(self, schema_registry_api):
        with pytest.raises(HTTPException) as exc:
            schema_registry_api.get_schema_by_subject("")
        
        assert exc.value.status_code == 400
        assert "subject" in str(exc.value.detail)


class TestSchemaRegistryAPIGetLatestSchema:
    def test_get_latest_schema_success(self, schema_registry_api, mock_schema_registry):
        mock_schema_registry.get_latest_schema.return_value = SchemaInfo(
            subject="test-subject",
            schema_id=1,
            schema_type=SchemaType.AVRO,
            schema='{"type":"record"}',
            version=1
        )
        
        response = schema_registry_api.get_latest_schema("test-subject")
        
        assert response.subject == "test-subject"

    def test_get_latest_schema_empty_subject_raises_400(self, schema_registry_api):
        with pytest.raises(HTTPException) as exc:
            schema_registry_api.get_latest_schema("")
        
        assert exc.value.status_code == 400
        assert "subject" in str(exc.value.detail)

    def test_get_latest_schema_not_found_raises_404(self, schema_registry_api, mock_schema_registry):
        mock_schema_registry.get_latest_schema.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            schema_registry_api.get_latest_schema("test-subject")
        
        assert exc.value.status_code == 404


class TestSchemaRegistryAPICheckCompatibility:
    def test_check_compatibility_success(self, schema_registry_api, mock_schema_registry):
        request = SchemaCompatibilityRequest(
            subject="test-subject",
            schema='{"type":"record"}',
            schema_type=SchemaType.AVRO
        )
        mock_schema_registry.check_compatibility.return_value = True
        
        response = schema_registry_api.check_compatibility(request)
        
        assert response["compatible"] is True

    def test_check_compatibility_empty_subject_raises_400(self, schema_registry_api):
        request = SchemaCompatibilityRequest(
            subject="",
            schema='{"type":"record"}',
            schema_type=SchemaType.AVRO
        )
        
        with pytest.raises(HTTPException) as exc:
            schema_registry_api.check_compatibility(request)
        
        assert exc.value.status_code == 400
        assert "subject" in str(exc.value.detail)


class TestSchemaRegistryAPIListSubjects:
    def test_list_subjects_success(self, schema_registry_api, mock_schema_registry):
        mock_schema_registry.list_subjects.return_value = ["subject1", "subject2"]
        
        response = schema_registry_api.list_subjects()
        
        assert response["subjects"] == ["subject1", "subject2"]


class TestSchemaRegistryAPIListVersions:
    def test_list_versions_success(self, schema_registry_api, mock_schema_registry):
        mock_schema_registry.list_versions.return_value = [1, 2, 3]
        
        response = schema_registry_api.list_versions("test-subject")
        
        assert response["versions"] == [1, 2, 3]

    def test_list_versions_empty_subject_raises_400(self, schema_registry_api):
        with pytest.raises(HTTPException) as exc:
            schema_registry_api.list_versions("")
        
        assert exc.value.status_code == 400
        assert "subject" in str(exc.value.detail)


class TestSchemaRegistryAPIDeleteSubject:
    def test_delete_subject_success(self, schema_registry_api, mock_schema_registry):
        mock_schema_registry.delete_subject.return_value = True
        
        response = schema_registry_api.delete_subject("test-subject")
        
        assert response["success"] is True

    def test_delete_subject_empty_subject_raises_400(self, schema_registry_api):
        with pytest.raises(HTTPException) as exc:
            schema_registry_api.delete_subject("")
        
        assert exc.value.status_code == 400
        assert "subject" in str(exc.value.detail)


class TestSchemaRegistryAPIUpdateCompatibility:
    def test_update_compatibility_success(self, schema_registry_api, mock_schema_registry):
        request = CompatibilityUpdateRequest(
            subject="test-subject",
            compatibility="BACKWARD"
        )
        mock_schema_registry.update_compatibility.return_value = True
        
        response = schema_registry_api.update_compatibility(request)
        
        assert response["success"] is True

    def test_update_compatibility_empty_subject_raises_400(self, schema_registry_api):
        request = CompatibilityUpdateRequest(
            subject="",
            compatibility="BACKWARD"
        )
        
        with pytest.raises(HTTPException) as exc:
            schema_registry_api.update_compatibility(request)
        
        assert exc.value.status_code == 400
        assert "subject" in str(exc.value.detail)

    def test_update_compatibility_invalid_compat_raises_400(self, schema_registry_api):
        request = CompatibilityUpdateRequest(
            subject="test-subject",
            compatibility="INVALID"
        )
        
        with pytest.raises(HTTPException) as exc:
            schema_registry_api.update_compatibility(request)
        
        assert exc.value.status_code == 400
        assert "compatibility" in str(exc.value.detail)


class TestSchemaRegistryAPISerialize:
    def test_serialize_success(self, schema_registry_api, mock_schema_registry):
        request = SerializationRequest(
            subject="test-subject",
            data={"key": "value"},
            schema_id=1
        )
        mock_schema_registry.serialize.return_value = b"serialized-data"
        
        response = schema_registry_api.serialize(request)
        
        assert response.data is not None

    def test_serialize_empty_subject_raises_400(self, schema_registry_api):
        request = SerializationRequest(
            subject="",
            data={"key": "value"},
            schema_id=1
        )
        
        with pytest.raises(HTTPException) as exc:
            schema_registry_api.serialize(request)
        
        assert exc.value.status_code == 400
        assert "subject" in str(exc.value.detail)


class TestSchemaRegistryAPIDeserialize:
    def test_deserialize_success(self, schema_registry_api, mock_schema_registry):
        import base64
        request = DeserializationRequest(
            data=base64.b64encode(b"serialized-data").decode('utf-8'),
            schema_id=1
        )
        mock_schema_registry.deserialize.return_value = {"key": "value"}
        
        response = schema_registry_api.deserialize(request)
        
        assert response.data is not None

    def test_deserialize_empty_data_raises_400(self, schema_registry_api):
        request = DeserializationRequest(
            data="",
            schema_id=1
        )
        
        with pytest.raises(HTTPException) as exc:
            schema_registry_api.deserialize(request)
        
        assert exc.value.status_code == 400
        assert "data" in str(exc.value.detail)
