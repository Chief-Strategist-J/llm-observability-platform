"""Schema registry business logic service."""

from typing import Any, Dict, List, Optional

from opentelemetry import trace
from ...shared.errors.codes import validation_failed, business_error
from ...shared.utils.validation import validate_schema_request
from ...shared.ports.schema_registry_port import SchemaRegistryPort, SchemaType, SchemaInfo


class SchemaRegistryService:
    """Business logic for schema registry operations with SRP compliance."""
    
    def __init__(self, schema_registry: SchemaRegistryPort):
        self.schema_registry = schema_registry
        self.tracer = trace.get_tracer(__name__)
    
    def register_schema(self, schema_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new schema with validation."""
        with self.tracer.start_as_current_span("schema_registry.register_schema") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "register_schema")
            
            try:
                # Validate input
                is_valid, error = validate_schema_request(schema_data)
                if not is_valid:
                    span.record_error(error or "Invalid schema request")
                    raise validation_failed(error or "Invalid schema request")
                
                subject = schema_data['subject']
                schema = schema_data['schema']
                schema_type = SchemaType(schema_data['schema_type'])
                
                # Check if schema already exists (business rule)
                try:
                    existing_schema = self.schema_registry.get_latest_schema(subject)
                    if existing_schema.schema == schema:
                        return {
                            "schema_id": existing_schema.schema_id,
                            "subject": subject,
                            "version": existing_schema.version,
                            "message": "Schema already exists",
                            "duplicate": True
                        }
                except Exception:
                    # Schema doesn't exist, continue with registration
                    pass
                
                # Register schema
                schema_id = self.schema_registry.register_schema(subject, schema, schema_type)
                
                span.set_attribute("subject", subject)
                span.set_attribute("schema_id", str(schema_id))
                span.set_attribute("success", "true")
                
                return {
                    "schema_id": schema_id,
                    "subject": subject,
                    "version": 1,  # New schema starts at version 1
                    "duplicate": False
                }
                
                raise
            except Exception as e:
                raise business_error(f"Processing failed: {str(e)}")
    
    def get_schema(self, schema_id: int) -> Dict[str, Any]:
        """Get schema by ID."""
        with self.tracer.start_as_current_span("schema_registry.get_schema") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "get_schema")
            span.set_attribute("schema_id", str(schema_id))
            
            try:
                schema_info = self.schema_registry.get_schema(schema_id)
                
                return {
                    "subject": schema_info.subject,
                    "schema_id": schema_info.schema_id,
                    "schema_type": schema_info.schema_type.value,
                    "schema": schema_info.schema,
                    "version": schema_info.version,
                    "compatibility": schema_info.compatibility
                }
                
            except Exception as e:
                raise business_error(f"Processing failed: {str(e)}")
    
    def get_schema_by_subject(self, subject: str, version: Optional[int] = None) -> Dict[str, Any]:
        """Get schema by subject and version."""
        with self.tracer.start_as_current_span("schema_registry.get_schema_by_subject") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "get_schema_by_subject")
            span.set_attribute("subject", subject)
            span.set_attribute("version", str(version) if version else "latest")
            
            try:
                if version:
                    schema_info = self.schema_registry.get_schema_by_subject(subject, version)
                else:
                    schema_info = self.schema_registry.get_latest_schema(subject)
                
                return {
                    "subject": schema_info.subject,
                    "schema_id": schema_info.schema_id,
                    "schema_type": schema_info.schema_type.value,
                    "schema": schema_info.schema,
                    "version": schema_info.version,
                    "compatibility": schema_info.compatibility
                }
                
            except Exception as e:
                raise business_error(f"Processing failed: {str(e)}")
    
    def list_subjects(self) -> Dict[str, Any]:
        """List all subjects."""
        with self.tracer.start_as_current_span("schema_registry.list_subjects") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "list_subjects")
            
            try:
                subjects = self.schema_registry.list_subjects()
                
                return {
                    "subjects": subjects
                }
                
            except Exception as e:
                raise business_error(f"Processing failed: {str(e)}")
    
    def check_compatibility(self, compatibility_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check schema compatibility."""
        with self.tracer.start_as_current_span("schema_registry.check_compatibility") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "check_compatibility")
            
            try:
                # Validate input
                required_fields = ['subject', 'schema', 'schema_type']
                for field in required_fields:
                    if field not in compatibility_data:
                        span.record_error("Validation failed")
                    raise validation_failed("Validation failed")
                            code="VALIDATION_MISSING_FIELD",
                            message=f"Missing required field: {field}"
                        )
                        span.record_error(validation_error)
                        raise validation_error
                
                subject = compatibility_data['subject']
                schema = compatibility_data['schema']
                schema_type = SchemaType(compatibility_data['schema_type'])
                
                # Check compatibility
                is_compatible = self.schema_registry.check_compatibility(subject, schema, schema_type)
                
                return {
                    "is_compatible": is_compatible,
                    "subject": subject,
                    "message": "Schema is compatible" if is_compatible else "Schema is not compatible"
                }
                
                raise
            except Exception as e:
                raise business_error(f"Processing failed: {str(e)}")
    
    def update_compatibility(self, subject: str, compatibility: str) -> Dict[str, Any]:
        """Update compatibility level for subject."""
        with self.tracer.start_as_current_span("schema_registry.update_compatibility") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "update_compatibility")
            span.set_attribute("subject", subject)
            span.set_attribute("compatibility", compatibility)
            
            try:
                # Validate compatibility level
                valid_levels = ['BACKWARD', 'FORWARD', 'FULL', 'NONE']
                if compatibility not in valid_levels:
                    span.record_error("Validation failed")
                    raise validation_failed("Validation failed")
                        code="VALIDATION_INVALID_FORMAT",
                        message=f"Invalid compatibility level: {compatibility}. Must be one of {valid_levels}"
                    )
                    span.record_error(validation_error)
                    raise validation_error
                
                # Update compatibility
                success = self.schema_registry.update_compatibility(subject, compatibility)
                
                if success:
                    return {
                        "subject": subject,
                        "compatibility": compatibility,
                        "message": "Compatibility level updated successfully"
                    }
                else:
                    span.record_error(f"Business rule violation")
                    raise business_error(f"Business rule violation")
                        code="BUSINESS_PROCESSING_FAILED",
                        message="Failed to update compatibility level"
                    )
                    span.record_error(business_error)
                    raise business_error
                
                raise
            except Exception as e:
                raise business_error(f"Processing failed: {str(e)}")
    
    def serialize_data(self, serialization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize data using schema."""
        with self.tracer.start_as_current_span("schema_registry.serialize_data") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "serialize_data")
            
            try:
                # Validate input
                required_fields = ['subject', 'data']
                for field in required_fields:
                    if field not in serialization_data:
                        span.record_error("Validation failed")
                    raise validation_failed("Validation failed")
                            code="VALIDATION_MISSING_FIELD",
                            message=f"Missing required field: {field}"
                        )
                        span.record_error(validation_error)
                        raise validation_error
                
                subject = serialization_data['subject']
                data = serialization_data['data']
                schema_id = serialization_data.get('schema_id')
                
                # Serialize data
                serialized_bytes = self.schema_registry.serialize(subject, data, schema_id)
                
                # Convert to base64 for JSON transport
                import base64
                serialized_data = base64.b64encode(serialized_bytes).decode('ascii')
                
                return {
                    "data": serialized_data,
                    "schema_id": schema_id,
                    "subject": subject
                }
                
                raise
            except Exception as e:
                raise business_error(f"Processing failed: {str(e)}")
    
    def deserialize_data(self, deserialization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize data using schema."""
        with self.tracer.start_as_current_span("schema_registry.deserialize_data") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "deserialize_data")
            
            try:
                # Validate input
                required_fields = ['data', 'schema_id']
                for field in required_fields:
                    if field not in deserialization_data:
                        span.record_error("Validation failed")
                    raise validation_failed("Validation failed")
                            code="VALIDATION_MISSING_FIELD",
                            message=f"Missing required field: {field}"
                        )
                        span.record_error(validation_error)
                        raise validation_error
                
                data = deserialization_data['data']
                schema_id = deserialization_data['schema_id']
                
                # Decode from base64
                import base64
                decoded_bytes = base64.b64decode(data)
                
                # Deserialize data
                deserialized_obj = self.schema_registry.deserialize(decoded_bytes, schema_id)
                
                return {
                    "data": deserialized_obj,
                    "schema_id": schema_id
                }
                
                raise
            except Exception as e:
                raise business_error(f"Processing failed: {str(e)}")
