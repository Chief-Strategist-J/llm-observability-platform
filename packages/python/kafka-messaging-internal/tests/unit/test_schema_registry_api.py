"""Unit tests for Schema Registry API handlers."""

import pytest
from typing import Dict
from unittest.mock import Mock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from kafka_messaging_internal.api.rest.v1.handlers.schema_registry import (
    SchemaRegistryAPI, 
    SchemaRegisterRequest, 
    SchemaCompatibilityRequest,
    CompatibilityUpdateRequest,
    SerializationRequest,
    DeserializationRequest
)
from kafka_messaging_internal.shared.ports.schema_registry_port import SchemaRegistryPort
from kafka_messaging_internal.shared.types.schema import SchemaType, SchemaInfo


class TestSchemaRegistryAPI:
    """Test cases for Schema Registry API handlers"""

    @pytest.fixture
    def mock_schema_registry(self):
        """Mock schema registry port"""
        schema_registry = Mock(spec=SchemaRegistryPort)
        schema_registry.register_schema = Mock(return_value=123)
        schema_registry.list_subjects = Mock(return_value=["test-subject"])
        schema_registry.get_schema_by_subject = Mock(return_value=SchemaInfo(
            subject="test-subject",
            schema_id=123,
            schema_type=SchemaType.JSON,
            schema='{"type": "object"}',
            version=1
        ))
        schema_registry.check_compatibility = Mock(return_value=True)
        schema_registry.update_compatibility = Mock(return_value=True)
        schema_registry.serialize = Mock(return_value=b"serialized_data")
        schema_registry.deserialize = Mock(return_value={"deserialized": "data"})
        return schema_registry

    @pytest.fixture
    def schema_registry_api(self, mock_schema_registry):
        """Create schema registry API instance"""
        return SchemaRegistryAPI(mock_schema_registry)

    @pytest.fixture
    def app(self, schema_registry_api):
        """Create FastAPI app for testing"""
        app = FastAPI()
        app.include_router(schema_registry_api.get_router(), prefix="/api/v1/schema-registry")
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)

    def test_register_schema_success(self, client, mock_schema_registry):
        request_data = {
            "subject": "test-subject",
            "schema_definition": '{"type": "object"}',
            "schema_type": "JSON"
        }
        
        response = client.post("/api/v1/schema-registry/schemas", json=request_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["subject"] == "test-subject"
        assert data["schema_id"] == 123
        assert data["version"] == 1
        mock_schema_registry.register_schema.assert_called_once_with(
            "test-subject", '{"type": "object"}', SchemaType.JSON
        )

    def test_register_schema_validation_error(self, client):
        request_data = {
            "schema_definition": '{"type": "object"}',
            "schema_type": "JSON"
        }
        
        response = client.post("/api/v1/schema-registry/schemas", json=request_data)
        
        assert response.status_code == 422

    def test_list_subjects_success(self, client, mock_schema_registry):
        """Test successful subject listing"""
        response = client.get("/api/v1/schema-registry/schemas")
        
        assert response.status_code == 200
        data = response.json()
        assert data["subjects"] == ["test-subject"]
        mock_schema_registry.list_subjects.assert_called_once()

    def test_get_schema_by_subject_success(self, client, mock_schema_registry):
        """Test successful schema retrieval by subject"""
        response = client.get("/api/v1/schema-registry/schemas/test-subject")
        
        assert response.status_code == 200
        data = response.json()
        assert data["subject"] == "test-subject"
        assert data["schema_id"] == 123
        assert data["schema_type"] == "JSON"
        assert data["version"] == 1
        mock_schema_registry.get_schema_by_subject.assert_called_once_with("test-subject", None)

    def test_get_schema_by_subject_with_version(self, client, mock_schema_registry):
        """Test schema retrieval with specific version"""
        response = client.get("/api/v1/schema-registry/schemas/test-subject?version=2")
        
        assert response.status_code == 200
        mock_schema_registry.get_schema_by_subject.assert_called_once_with("test-subject", 2)

    def test_get_schema_not_found(self, client, mock_schema_registry):
        """Test schema retrieval when not found"""
        mock_schema_registry.get_schema_by_subject.side_effect = Exception("Schema not found")
        
        response = client.get("/api/v1/schema-registry/schemas/nonexistent-subject")
        
        assert response.status_code == 404

    def test_check_compatibility_success(self, client, mock_schema_registry):
        request_data = {
            "subject": "test-subject",
            "schema_definition": '{"type": "object", "properties": {"new_field": {"type": "string"}}}',
            "schema_type": "JSON"
        }
        
        response = client.post("/api/v1/schema-registry/compatibility", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_compatible"] is True
        assert "compatibility_level" in data
        assert "message" in data
        mock_schema_registry.check_compatibility.assert_called_once()

    def test_check_compatibility_incompatible(self, client, mock_schema_registry):
        mock_schema_registry.check_compatibility.return_value = False
        
        request_data = {
            "subject": "test-subject",
            "schema_definition": '{"type": "string"}',
            "schema_type": "JSON"
        }
        
        response = client.post("/api/v1/schema-registry/compatibility", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_compatible"] is False

    def test_update_compatibility_success(self, client, mock_schema_registry):
        """Test successful compatibility update"""
        request_data = {
            "subject": "test-subject",
            "compatibility": "BACKWARD"
        }
        
        response = client.put("/api/v1/schema-registry/compatibility/test-subject", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["subject"] == "test-subject"
        assert data["compatibility"] == "BACKWARD"
        assert data["success"] is True
        mock_schema_registry.update_compatibility.assert_called_once_with("test-subject", "BACKWARD")

    def test_update_compatibility_not_found(self, client, mock_schema_registry):
        """Test compatibility update when subject not found"""
        mock_schema_registry.update_compatibility.return_value = False
        
        request_data = {
            "subject": "nonexistent-subject",
            "compatibility": "BACKWARD"
        }
        
        response = client.put("/api/v1/schema-registry/compatibility/nonexistent-subject", json=request_data)
        
        assert response.status_code == 404

    def test_serialize_data_success(self, client, mock_schema_registry):
        """Test successful data serialization"""
        request_data = {
            "subject": "test-subject",
            "data": {"field": "value"}
        }
        
        response = client.post("/api/v1/schema-registry/serialize", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "schema_id" in data
        mock_schema_registry.serialize.assert_called_once_with("test-subject", {"field": "value"}, None)

    def test_serialize_data_with_schema_id(self, client, mock_schema_registry):
        """Test data serialization with specific schema ID"""
        request_data = {
            "subject": "test-subject",
            "data": {"field": "value"},
            "schema_id": 123
        }
        
        response = client.post("/api/v1/schema-registry/serialize", json=request_data)
        
        assert response.status_code == 200
        mock_schema_registry.serialize.assert_called_once_with("test-subject", {"field": "value"}, 123)

    def test_deserialize_data_success(self, client, mock_schema_registry):
        """Test successful data deserialization"""
        import base64
        test_data = base64.b64encode(b'{"field": "value"}').decode('utf-8')
        
        request_data = {
            "data": test_data,
            "schema_id": 123
        }
        
        response = client.post("/api/v1/schema-registry/deserialize", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == {"deserialized": "data"}
        assert data["schema_id"] == 123
        mock_schema_registry.deserialize.assert_called_once()

    def test_deserialize_data_invalid_base64(self, client):
        """Test deserialization with invalid base64 data"""
        request_data = {
            "data": "invalid_base64!",
            "schema_id": 123
        }
        
        response = client.post("/api/v1/schema-registry/deserialize", json=request_data)
        
        assert response.status_code == 500
