"""Schema registry client with single responsibility."""

import logging
from typing import List, Dict, Any, Optional
from opentelemetry import trace

from shared.errors.codes import http_request_failed

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


class SchemaRegistryClient:
    """Client for schema registry operations with single responsibility"""
    
    def __init__(self, base_client):
        self._client = base_client
        self._base_path = "/api/v1/schema-registry"
    
    def register_schema(self, subject: str, schema: str, 
                        schema_type: str = "AVRO") -> Dict[str, Any]:
        """Register new schema"""
        with _tracer.start_as_current_span("register_schema") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "schema-registry-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("subject", subject)
            span.set_attribute("schema.type", schema_type)
            
            try:
                data = {
                    "subject": subject,
                    "schema": schema,
                    "schema_type": schema_type
                }
                result = self._client.post(f"{self._base_path}/schemas", data=data)
                span.set_attribute("client.result", "success")
                span.set_attribute("schema.id", str(result.get("id", "")))
                logger.info("event=schema_registered subject=%s id=%s", subject, result.get("id", ""))
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=schema_register_failed subject=%s error=%s", subject, str(e))
                raise http_request_failed(f"Failed to register schema: {str(e)}")
    
    def get_schema(self, schema_id: int) -> Dict[str, Any]:
        """Get schema by ID"""
        with _tracer.start_as_current_span("get_schema") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "schema-registry-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("schema.id", str(schema_id))
            
            try:
                result = self._client.get(f"{self._base_path}/schemas/{schema_id}")
                span.set_attribute("client.result", "success")
                span.set_attribute("schema.subject", result.get("subject", ""))
                logger.info("event=schema_retrieved id=%d subject=%s", schema_id, result.get("subject", ""))
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=schema_retrieve_failed id=%d error=%s", schema_id, str(e))
                raise http_request_failed(f"Failed to get schema: {str(e)}")
    
    def get_schema_by_subject(self, subject: str, 
                             version: Optional[int] = None) -> Dict[str, Any]:
        """Get schema by subject and version"""
        with _tracer.start_as_current_span("get_schema_by_subject") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "schema-registry-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("subject", subject)
            if version:
                span.set_attribute("schema.version", str(version))
            
            try:
                if version:
                    result = self._client.get(f"{self._base_path}/subjects/{subject}/versions/{version}")
                else:
                    result = self._client.get(f"{self._base_path}/subjects/{subject}/latest")
                
                span.set_attribute("client.result", "success")
                span.set_attribute("schema.id", str(result.get("id", "")))
                logger.info("event=schema_retrieved_by_subject subject=%s version=%s", subject, version or "latest")
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=schema_retrieve_by_subject_failed subject=%s version=%s error=%s", subject, version or "latest", str(e))
                raise http_request_failed(f"Failed to get schema by subject: {str(e)}")
    
    def get_latest_schema(self, subject: str) -> Dict[str, Any]:
        """Get latest schema for subject"""
        with _tracer.start_as_current_span("get_latest_schema") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "schema-registry-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("subject", subject)
            
            try:
                result = self._client.get(f"{self._base_path}/subjects/{subject}/latest")
                span.set_attribute("client.result", "success")
                span.set_attribute("schema.id", str(result.get("id", "")))
                logger.info("event=latest_schema_retrieved subject=%s id=%s", subject, result.get("id", ""))
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=latest_schema_retrieve_failed subject=%s error=%s", subject, str(e))
                raise http_request_failed(f"Failed to get latest schema: {str(e)}")
    
    def list_subjects(self) -> Dict[str, List[str]]:
        """List all subjects"""
        with _tracer.start_as_current_span("list_subjects") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "schema-registry-client")
            span.set_attribute("api.version", "v1")
            
            try:
                result = self._client.get(f"{self._base_path}/subjects")
                subjects = result.get("subjects", [])
                span.set_attribute("client.result", "success")
                span.set_attribute("subjects.count", str(len(subjects)))
                logger.info("event=subjects_listed count=%d", len(subjects))
                return {"subjects": subjects}
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=subjects_list_failed error=%s", str(e))
                raise http_request_failed(f"Failed to list subjects: {str(e)}")
    
    def get_schema_versions(self, subject: str) -> Dict[str, List[int]]:
        """Get all versions for subject"""
        with _tracer.start_as_current_span("get_schema_versions") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "schema-registry-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("subject", subject)
            
            try:
                result = self._client.get(f"{self._base_path}/subjects/{subject}/versions")
                versions = result.get("versions", [])
                span.set_attribute("client.result", "success")
                span.set_attribute("versions.count", str(len(versions)))
                logger.info("event=schema_versions_retrieved subject=%s count=%d", subject, len(versions))
                return {"versions": versions}
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=schema_versions_retrieve_failed subject=%s error=%s", subject, str(e))
                raise http_request_failed(f"Failed to get schema versions: {str(e)}")
    
    def check_compatibility(self, subject: str, schema: str, 
                          version: Optional[str] = None) -> Dict[str, bool]:
        """Check schema compatibility"""
        with _tracer.start_as_current_span("check_compatibility") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "schema-registry-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("subject", subject)
            
            try:
                data = {
                    "schema": schema,
                    "version": version or "latest"
                }
                result = self._client.post(f"{self._base_path}/compatibility/subjects/{subject}", data=data)
                span.set_attribute("client.result", "success")
                span.set_attribute("is.compatible", str(result.get("is_compatible", False)))
                logger.info("event=compatibility_checked subject=%s compatible=%s", subject, result.get("is_compatible", False))
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=compatibility_check_failed subject=%s error=%s", subject, str(e))
                raise http_request_failed(f"Failed to check compatibility: {str(e)}")
    
    def close(self):
        """Close client"""
        with _tracer.start_as_current_span("close_schema_registry_client") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "schema-registry-client")
            span.set_attribute("api.version", "v1")
            
            try:
                self._client.close()
                span.set_attribute("close.result", "success")
                logger.info("event=schema_registry_client_closed")
            except Exception as e:
                span.record_error(e)
                span.set_attribute("close.result", "failed")
                logger.error("event=schema_registry_client_close_error error=%s", str(e))
