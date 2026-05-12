"""Schema registry port interface."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from shared.types.schema import SchemaInfo, SchemaType


class SchemaRegistryPort(ABC):
    """Schema registry operations port interface."""
    
    @abstractmethod
    def register_schema(self, subject: str, schema: str, schema_type: SchemaType) -> int:
        """Register a new schema."""
        pass

    @abstractmethod
    def get_schema(self, schema_id: int) -> SchemaInfo:
        """Get schema by ID."""
        pass

    @abstractmethod
    def get_schema_by_subject(self, subject: str, version: Optional[int] = None) -> SchemaInfo:
        """Get schema by subject and version."""
        pass

    @abstractmethod
    def get_latest_schema(self, subject: str) -> SchemaInfo:
        """Get latest schema for subject."""
        pass

    @abstractmethod
    def list_subjects(self) -> List[str]:
        """List all subjects."""
        pass

    @abstractmethod
    def list_versions(self, subject: str) -> List[int]:
        """List all versions for a subject."""
        pass

    @abstractmethod
    def delete_subject(self, subject: str) -> bool:
        """Delete a subject and all its versions."""
        pass

    @abstractmethod
    def check_compatibility(self, subject: str, schema: str, schema_type: SchemaType) -> bool:
        """Check if schema is compatible with existing versions."""
        pass

    @abstractmethod
    def update_compatibility(self, subject: str, compatibility: str) -> bool:
        """Update compatibility level for a subject."""
        pass

    @abstractmethod
    def serialize(self, subject: str, data: Any, schema_id: Optional[int] = None) -> bytes:
        """Serialize data using schema."""
        pass

    @abstractmethod
    def deserialize(self, data: bytes, schema_id: Optional[int] = None) -> Any:
        """Deserialize data using schema."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close schema registry connection."""
        pass
