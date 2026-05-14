"""Public interface for schema registry feature."""

from typing import Any, Dict, List, Optional
from opentelemetry import trace
from .service import SchemaRegistryService
from kafka_messaging_internal.shared.di.container import get_container
from kafka_messaging_internal.shared.ports.schema_registry_port import SchemaRegistryPort, SchemaType
from kafka_messaging_internal.shared.errors.exceptions import ValidationError


class SchemaRegistry:
    """Schema registry feature entry point following SRP rules."""
    
    def __init__(self):
        self.tracer = trace.get_tracer(__name__)
        self.container = get_container()
        
        with self.tracer.start_as_current_span("schema_registry_initialization") as span:
            span.set_attributes({
                "service.name": "kafka-messaging-internal",
                "feature.name": "schema_registry",
                "api.version": "v1"
            })
            
            try:
                self.schema_registry = self.container.get(SchemaRegistryPort)
                self.service = SchemaRegistryService(self.schema_registry)
                
                span.set_status(trace.Status(trace.StatusCode.OK))
                
            except Exception as e:
                span.record_error(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
    
    async def register_schema(self, schema_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new schema."""
        return await self.service.register_schema(schema_data)
    
    async def get_schema(self, schema_id: int) -> Dict[str, Any]:
        """Get schema by ID."""
        return await self.service.get_schema(schema_id)
    
    async def get_schema_by_subject(self, subject: str, version: Optional[int] = None) -> Dict[str, Any]:
        """Get schema by subject and version."""
        return await self.service.get_schema_by_subject(subject, version)
    
    async def list_subjects(self) -> Dict[str, Any]:
        """List all subjects."""
        return await self.service.list_subjects()
    
    async def check_compatibility(self, compatibility_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check schema compatibility."""
        return await self.service.check_compatibility_api(compatibility_data)
    
    async def check_compatibility_api(self, compatibility_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check schema compatibility (alias for router)."""
        return await self.service.check_compatibility_api(compatibility_data)
    
    async def update_compatibility(self, subject: str, compatibility: str) -> Dict[str, Any]:
        """Update compatibility level for subject."""
        return await self.service.update_compatibility_api(subject, compatibility)
    
    async def update_compatibility_api(self, subject: str, compatibility: str) -> Dict[str, Any]:
        """Update compatibility level for subject (alias for router)."""
        return await self.service.update_compatibility_api(subject, compatibility)
    
    async def serialize_data(self, serialization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize data using schema."""
        return await self.service.serialize_data_dict(serialization_data)
    
    async def deserialize_data(self, deserialization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize data using schema."""
        return await self.service.deserialize_data_dict(deserialization_data)


# Factory function for DI container
def create_schema_registry() -> SchemaRegistry:
    """Create schema registry feature instance."""
    return SchemaRegistry()
