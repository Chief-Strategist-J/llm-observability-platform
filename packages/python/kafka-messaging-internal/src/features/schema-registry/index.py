"""Public interface for schema registry feature."""

from typing import Any, Dict, List, Optional
from .service import SchemaRegistryService
from ...shared.di.container import get_container
from ...shared.ports.schema_registry_port import SchemaRegistryPort, SchemaType


class SchemaRegistry:
    """Schema registry feature entry point following SRP rules."""
    
    def __init__(self):
        self.container = get_container()
        self.schema_registry = self.container.get(SchemaRegistryPort)
        self.service = SchemaRegistryService(self.schema_registry)
    
    def register_schema(self, schema_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new schema."""
        return self.service.register_schema(schema_data)
    
    def get_schema(self, schema_id: int) -> Dict[str, Any]:
        """Get schema by ID."""
        return self.service.get_schema(schema_id)
    
    def get_schema_by_subject(self, subject: str, version: Optional[int] = None) -> Dict[str, Any]:
        """Get schema by subject and version."""
        return self.service.get_schema_by_subject(subject, version)
    
    def list_subjects(self) -> Dict[str, Any]:
        """List all subjects."""
        return self.service.list_subjects()
    
    def check_compatibility(self, compatibility_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check schema compatibility."""
        return self.service.check_compatibility(compatibility_data)
    
    def update_compatibility(self, subject: str, compatibility: str) -> Dict[str, Any]:
        """Update compatibility level for subject."""
        return self.service.update_compatibility(subject, compatibility)
    
    def serialize_data(self, serialization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize data using schema."""
        return self.service.serialize_data(serialization_data)
    
    def deserialize_data(self, deserialization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize data using schema."""
        return self.service.deserialize_data(deserialization_data)


# Factory function for DI container
def create_schema_registry() -> SchemaRegistry:
    """Create schema registry feature instance."""
    return SchemaRegistry()
