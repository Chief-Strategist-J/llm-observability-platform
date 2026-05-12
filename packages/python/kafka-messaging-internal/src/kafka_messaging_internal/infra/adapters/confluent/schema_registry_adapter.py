"""Confluent Schema Registry adapter implementing SchemaRegistryPort."""

import json
import requests
from typing import Any, Dict, List, Optional
from base64 import b64encode, b64decode

from opentelemetry import trace
from kafka_messaging_internal.shared.errors.exceptions import map_adapter_error, SchemaRegistryError
from kafka_messaging_internal.shared.ports.schema_registry_port import SchemaRegistryPort, SchemaType, SchemaInfo


class ConfluentSchemaRegistryAdapter(SchemaRegistryPort):
    """Confluent Schema Registry implementation with tracing and error mapping."""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.base_url = config.get('SCHEMA_REGISTRY_URL', 'http://localhost:8081')
        self.auth = self._get_auth(config)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({'Content-Type': 'application/json'})
        self.tracer = trace.get_tracer(__name__)
    
    def _get_auth(self, config: Dict[str, str]) -> Optional[tuple]:
        """Get authentication credentials from config."""
        username = config.get('SCHEMA_REGISTRY_AUTH_USERNAME')
        password = config.get('SCHEMA_REGISTRY_AUTH_PASSWORD')
        if username and password:
            return (username, password)
        return None
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> requests.Response:
        """Make HTTP request with tracing and error handling."""
        with self.tracer.start_as_current_span("schema_registry.request") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", method.lower())
            span.set_attribute("endpoint", endpoint)
            
            url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            try:
                if method.upper() == 'GET':
                    response = self.session.get(url)
                elif method.upper() == 'POST':
                    response = self.session.post(url, json=data)
                elif method.upper() == 'PUT':
                    response = self.session.put(url, json=data)
                elif method.upper() == 'DELETE':
                    response = self.session.delete(url)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                span.set_attribute("http.status_code", str(response.status_code))
                
                if response.status_code >= 400:
                    error_msg = response.text or f"HTTP {response.status_code}"
                    if response.status_code == 404:
                        error = map_adapter_error('schema_registry', 'schema_not_found', Exception(error_msg))
                    elif response.status_code >= 400 and response.status_code < 500:
                        error = map_adapter_error('schema_registry', 'invalid_schema', Exception(error_msg))
                    else:
                        error = map_adapter_error('schema_registry', 'connection_failed', Exception(error_msg))
                    span.record_error(error)
                    raise error
                
                return response
                
            except requests.exceptions.RequestException as e:
                error = map_adapter_error('schema_registry', 'connection_failed', e)
                span.record_error(error)
                raise error
    
    def register_schema(self, subject: str, schema: str, schema_type: SchemaType) -> int:
        """Register a new schema."""
        with self.tracer.start_as_current_span("schema_registry.register_schema") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "register_schema")
            span.set_attribute("subject", subject)
            span.set_attribute("schema_type", schema_type.value)
            
            data = {
                "schema": schema,
                "schemaType": schema_type.value
            }
            
            try:
                response = self._make_request('POST', f'/subjects/{subject}/versions', data)
                result = response.json()
                return result.get('id')
            except Exception as e:
                span.record_error(e)
                raise
    
    def get_schema(self, schema_id: int) -> SchemaInfo:
        """Get schema by ID."""
        with self.tracer.start_as_current_span("schema_registry.get_schema") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "get_schema")
            span.set_attribute("schema_id", str(schema_id))
            
            try:
                response = self._make_request('GET', f'/schemas/ids/{schema_id}')
                result = response.json()
                
                return SchemaInfo(
                    subject=result.get('subject'),
                    schema_id=result.get('id'),
                    schema_type=SchemaType(result.get('schemaType')),
                    schema=result.get('schema'),
                    version=result.get('version'),
                    compatibility=result.get('compatibilityLevel')
                )
            except Exception as e:
                span.record_error(e)
                raise
    
    def get_schema_by_subject(self, subject: str, version: Optional[int] = None) -> SchemaInfo:
        """Get schema by subject and version."""
        with self.tracer.start_as_current_span("schema_registry.get_schema_by_subject") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "get_schema_by_subject")
            span.set_attribute("subject", subject)
            span.set_attribute("version", str(version) if version else "latest")
            
            try:
                if version:
                    endpoint = f'/subjects/{subject}/versions/{version}'
                else:
                    endpoint = f'/subjects/{subject}/versions/latest'
                
                response = self._make_request('GET', endpoint)
                result = response.json()
                
                return SchemaInfo(
                    subject=result.get('subject'),
                    schema_id=result.get('id'),
                    schema_type=SchemaType(result.get('schemaType')),
                    schema=result.get('schema'),
                    version=result.get('version'),
                    compatibility=result.get('compatibilityLevel')
                )
            except Exception as e:
                span.record_error(e)
                raise
    
    def get_latest_schema(self, subject: str) -> SchemaInfo:
        """Get latest schema for subject."""
        return self.get_schema_by_subject(subject, None)
    
    def list_subjects(self) -> List[str]:
        """List all subjects."""
        with self.tracer.start_as_current_span("schema_registry.list_subjects") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "list_subjects")
            
            try:
                response = self._make_request('GET', '/subjects')
                return response.json()
            except Exception as e:
                span.record_error(e)
                raise
    
    def list_versions(self, subject: str) -> List[int]:
        """List all versions for a subject."""
        with self.tracer.start_as_current_span("schema_registry.list_versions") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "list_versions")
            span.set_attribute("subject", subject)
            
            try:
                response = self._make_request('GET', f'/subjects/{subject}/versions')
                return response.json()
            except Exception as e:
                span.record_error(e)
                raise
    
    def delete_subject(self, subject: str) -> bool:
        """Delete a subject and all its versions."""
        with self.tracer.start_as_current_span("schema_registry.delete_subject") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "delete_subject")
            span.set_attribute("subject", subject)
            
            try:
                response = self._make_request('DELETE', f'/subjects/{subject}')
                return response.status_code == 200
            except Exception as e:
                span.record_error(e)
                raise
    
    def check_compatibility(self, subject: str, schema: str, schema_type: SchemaType) -> bool:
        """Check if schema is compatible with existing versions."""
        with self.tracer.start_as_current_span("schema_registry.check_compatibility") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "check_compatibility")
            span.set_attribute("subject", subject)
            span.set_attribute("schema_type", schema_type.value)
            
            data = {
                "schema": schema,
                "schemaType": schema_type.value
            }
            
            try:
                response = self._make_request('POST', f'/compatibility/subjects/{subject}/versions/latest', data)
                result = response.json()
                return result.get('is_compatible', False)
            except Exception as e:
                span.record_error(e)
                raise
    
    def update_compatibility(self, subject: str, compatibility: str) -> bool:
        """Update compatibility level for a subject."""
        with self.tracer.start_as_current_span("schema_registry.update_compatibility") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "update_compatibility")
            span.set_attribute("subject", subject)
            span.set_attribute("compatibility", compatibility)
            
            data = {"compatibility": compatibility}
            
            try:
                response = self._make_request('PUT', f'/config/{subject}', data)
                return response.status_code == 200
            except Exception as e:
                span.record_error(e)
                raise
    
    def serialize(self, subject: str, data: Any, schema_id: Optional[int] = None) -> bytes:
        """Serialize data using schema."""
        with self.tracer.start_as_current_span("schema_registry.serialize") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "serialize")
            span.set_attribute("subject", subject)
            span.set_attribute("schema_id", str(schema_id) if schema_id else "auto")
            
            # Get schema info
            if schema_id:
                schema_info = self.get_schema(schema_id)
            else:
                schema_info = self.get_latest_schema(subject)
            
            # For now, implement simple JSON serialization
            # In a real implementation, you'd use the appropriate Avro/Protobuf serializer
            json_data = json.dumps(data)
            return json_data.encode('utf-8')
    
    def deserialize(self, data: bytes, schema_id: Optional[int] = None) -> Any:
        """Deserialize data using schema."""
        with self.tracer.start_as_current_span("schema_registry.deserialize") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "deserialize")
            span.set_attribute("schema_id", str(schema_id) if schema_id else "auto")
            
            # Get schema info
            if schema_id:
                schema_info = self.get_schema(schema_id)
            else:
                raise ValueError("Schema ID is required for deserialization")
            
            # For now, implement simple JSON deserialization
            # In a real implementation, you'd use the appropriate Avro/Protobuf deserializer
            json_str = data.decode('utf-8')
            return json.loads(json_str)
    
    def close(self) -> None:
        """Close the adapter."""
        with self.tracer.start_as_current_span("schema_registry.close") as span:
            span.set_attribute("feature.name", "schema-registry")
            span.set_attribute("operation", "close")
            
            if hasattr(self, 'session') and self.session:
                self.session.close()
