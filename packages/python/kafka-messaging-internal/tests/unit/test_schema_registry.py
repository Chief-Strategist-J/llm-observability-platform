"""Unit tests for schema registry feature."""

import pytest
from unittest.mock import Mock

from kafka_messaging_internal.features.schema_registry.service import SchemaRegistryService
from kafka_messaging_internal.shared.errors.exceptions import ValidationError, BusinessError


class TestSchemaRegistryService:
    """Unit tests for SchemaRegistryService."""
    
    def test_register_schema_success(self, mock_schema_registry_port, sample_schema_data):
        """Test successful schema registration."""
        service = SchemaRegistryService(mock_schema_registry_port)
        
        # Mock schema doesn't exist
        mock_schema_registry_port.get_latest_schema.side_effect = Exception("Schema not found")
        mock_schema_registry_port.register_schema.return_value = 1
        
        result = service.register_schema(sample_schema_data)
        
        assert result["schema_id"] == 1
        assert result["subject"] == "test-subject"
        assert result["version"] == 1
        assert result["duplicate"] is False
        mock_schema_registry_port.register_schema.assert_called_once()
    
    def test_register_schema_duplicate(self, mock_schema_registry_port, sample_schema_data):
        """Test registering duplicate schema."""
        service = SchemaRegistryService(mock_schema_registry_port)
        
        # Mock existing schema
        mock_schema = Mock()
        mock_schema.schema = sample_schema_data["schema"]
        mock_schema_registry_port.get_latest_schema.return_value = mock_schema
        
        result = service.register_schema(sample_schema_data)
        
        assert result["duplicate"] is True
        assert result["schema_id"] > 0  # Should return existing schema ID
        mock_schema_registry_port.register_schema.assert_not_called()
    
    def test_register_schema_validation_error(self, mock_schema_registry_port):
        """Test schema registration with invalid data."""
        service = SchemaRegistryService(mock_schema_registry_port)
        
        invalid_data = {"subject": ""}  # Missing required fields
        
        with pytest.raises(ValidationError) as exc_info:
            service.register_schema(invalid_data)
        
        assert exc_info.value.code == "VALIDATION_INVALID_REQUEST"
    
    def test_get_schema_success(self, mock_schema_registry_port):
        """Test successful schema retrieval."""
        service = SchemaRegistryService(mock_schema_registry_port)
        
        # Mock schema info
        mock_schema_info = Mock()
        mock_schema_info.subject = "test-subject"
        mock_schema_info.schema_id = 1
        mock_schema_info.schema_type.value = "AVRO"
        mock_schema_info.schema = '{"type": "record"}'
        mock_schema_info.version = 1
        mock_schema_info.compatibility = "BACKWARD"
        
        mock_schema_registry_port.get_schema.return_value = mock_schema_info
        
        result = service.get_schema(1)
        
        assert result["subject"] == "test-subject"
        assert result["schema_id"] == 1
        assert result["schema_type"] == "AVRO"
        assert result["version"] == 1
        mock_schema_registry_port.get_schema.assert_called_once_with(1)
    
    def test_get_schema_by_subject_success(self, mock_schema_registry_port):
        """Test successful schema retrieval by subject."""
        service = SchemaRegistryService(mock_schema_registry_port)
        
        # Mock schema info
        mock_schema_info = Mock()
        mock_schema_info.subject = "test-subject"
        mock_schema_info.schema_id = 1
        mock_schema_info.schema_type.value = "AVRO"
        mock_schema_info.schema = '{"type": "record"}'
        mock_schema_info.version = 1
        mock_schema_info.compatibility = "BACKWARD"
        
        mock_schema_registry_port.get_latest_schema.return_value = mock_schema_info
        
        result = service.get_schema_by_subject("test-subject")
        
        assert result["subject"] == "test-subject"
        assert result["schema_id"] == 1
        assert result["version"] == 1
        mock_schema_registry_port.get_latest_schema.assert_called_once_with("test-subject")
    
    def test_get_schema_by_subject_with_version(self, mock_schema_registry_port):
        """Test successful schema retrieval by subject and version."""
        service = SchemaRegistryService(mock_schema_registry_port)
        
        # Mock schema info
        mock_schema_info = Mock()
        mock_schema_info.subject = "test-subject"
        mock_schema_info.schema_id = 1
        mock_schema_info.schema_type.value = "AVRO"
        mock_schema_info.schema = '{"type": "record"}'
        mock_schema_info.version = 2
        mock_schema_info.compatibility = "BACKWARD"
        
        mock_schema_registry_port.get_schema_by_subject.return_value = mock_schema_info
        
        result = service.get_schema_by_subject("test-subject", 2)
        
        assert result["subject"] == "test-subject"
        assert result["version"] == 2
        mock_schema_registry_port.get_schema_by_subject.assert_called_once_with("test-subject", 2)
    
    def test_list_subjects_success(self, mock_schema_registry_port):
        """Test successful subjects listing."""
        service = SchemaRegistryService(mock_schema_registry_port)
        
        mock_schema_registry_port.list_subjects.return_value = ["subject1", "subject2"]
        
        result = service.list_subjects()
        
        assert result["subjects"] == ["subject1", "subject2"]
        mock_schema_registry_port.list_subjects.assert_called_once()
    
    def test_check_compatibility_success(self, mock_schema_registry_port, sample_schema_data):
        """Test successful compatibility check."""
        service = SchemaRegistryService(mock_schema_registry_port)
        
        mock_schema_registry_port.check_compatibility.return_value = True
        
        result = service.check_compatibility(sample_schema_data)
        
        assert result["is_compatible"] is True
        assert result["subject"] == "test-subject"
        assert "compatible" in result["message"]
        mock_schema_registry_port.check_compatibility.assert_called_once()
    
    def test_check_compatibility_validation_error(self, mock_schema_registry_port):
        """Test compatibility check with invalid data."""
        service = SchemaRegistryService(mock_schema_registry_port)
        
        invalid_data = {"subject": ""}  # Missing required fields
        
        with pytest.raises(ValidationError) as exc_info:
            service.check_compatibility(invalid_data)
        
        assert exc_info.value.code == "VALIDATION_MISSING_FIELD"
    
    def test_update_compatibility_success(self, mock_schema_registry_port):
        """Test successful compatibility update."""
        service = SchemaRegistryService(mock_schema_registry_port)
        
        mock_schema_registry_port.update_compatibility.return_value = True
        
        result = service.update_compatibility("test-subject", "BACKWARD")
        
        assert result["subject"] == "test-subject"
        assert result["compatibility"] == "BACKWARD"
        assert "successfully" in result["message"]
        mock_schema_registry_port.update_compatibility.assert_called_once_with("test-subject", "BACKWARD")
    
    def test_update_compatibility_validation_error(self, mock_schema_registry_port):
        """Test compatibility update with invalid level."""
        service = SchemaRegistryService(mock_schema_registry_port)
        
        with pytest.raises(ValidationError) as exc_info:
            service.update_compatibility("test-subject", "INVALID")
        
        assert exc_info.value.code == "VALIDATION_INVALID_FORMAT"
        assert "BACKWARD" in str(exc_info.value.message)
    
    def test_update_compatibility_failure(self, mock_schema_registry_port):
        """Test compatibility update failure."""
        service = SchemaRegistryService(mock_schema_registry_port)
        
        mock_schema_registry_port.update_compatibility.return_value = False
        
        with pytest.raises(BusinessError) as exc_info:
            service.update_compatibility("test-subject", "BACKWARD")
        
        assert exc_info.value.code == "BUSINESS_PROCESSING_FAILED"
    
    def test_serialize_data_success(self, mock_schema_registry_port):
        """Test successful data serialization."""
        service = SchemaRegistryService(mock_schema_registry_port)
        
        mock_schema_registry_port.serialize.return_value = b"serialized-data"
        
        data = {"message": "test data"}
        request_data = {"subject": "test-subject", "data": data}
        
        result = service.serialize_data(request_data)
        
        assert "data" in result
        assert result["subject"] == "test-subject"
        mock_schema_registry_port.serialize.assert_called_once()
    
    def test_serialize_data_validation_error(self, mock_schema_registry_port):
        """Test data serialization with invalid data."""
        service = SchemaRegistryService(mock_schema_registry_port)
        
        invalid_data = {"data": "test"}  # Missing subject
        
        with pytest.raises(ValidationError) as exc_info:
            service.serialize_data(invalid_data)
        
        assert exc_info.value.code == "VALIDATION_MISSING_FIELD"
    
    def test_deserialize_data_success(self, mock_schema_registry_port):
        """Test successful data deserialization."""
        service = SchemaRegistryService(mock_schema_registry_port)
        
        mock_schema_registry_port.deserialize.return_value = {"message": "test data"}
        
        request_data = {"data": "c2VyaWFsaXplZC1kYXRh", "schema_id": 1}  # base64 encoded
        
        result = service.deserialize_data(request_data)
        
        assert result["data"] == {"message": "test data"}
        assert result["schema_id"] == 1
        mock_schema_registry_port.deserialize.assert_called_once()
    
    def test_deserialize_data_validation_error(self, mock_schema_registry_port):
        """Test data deserialization with invalid data."""
        service = SchemaRegistryService(mock_schema_registry_port)
        
        invalid_data = {"data": "test"}  # Missing schema_id
        
        with pytest.raises(ValidationError) as exc_info:
            service.deserialize_data(invalid_data)
        
        assert exc_info.value.code == "VALIDATION_MISSING_FIELD"
