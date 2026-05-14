"""Schema Registry port interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class SchemaType(Enum):
    """Schema types supported."""
    AVRO = "avro"
    JSON = "json"
    PROTOBUF = "protobuf"


@dataclass
class SchemaConfig:
    """Schema registry configuration."""
    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    timeout: int = 30


@dataclass
class Schema:
    """Schema definition."""
    id: Optional[int]
    version: int
    name: str
    schema_type: SchemaType
    definition: str
    compatibility: str = "BACKWARD"


@dataclass
class SchemaInfo:
    """Schema information for responses."""
    subject: str
    schema_id: int
    schema_type: SchemaType
    schema: str
    version: Optional[int] = None
    compatibility: Optional[str] = None


class SchemaRegistryPort(ABC):
    """Schema Registry interface following hexagonal architecture."""
    
    @abstractmethod
    async def register_schema(self, schema: Schema) -> int:
        """Register a new schema and return its ID."""
        pass
    
    @abstractmethod
    async def get_schema(self, schema_id: int) -> Schema:
        """Get schema by ID."""
        pass
    
    @abstractmethod
    async def get_schema_by_name(self, name: str, version: Optional[int] = None) -> Schema:
        """Get schema by name and optional version."""
        pass
    
    @abstractmethod
    async def list_schemas(self, subject: Optional[str] = None) -> List[Schema]:
        """List all schemas or schemas for a specific subject."""
        pass
    
    @abstractmethod
    async def validate_schema(self, schema_definition: str, schema_type: SchemaType) -> bool:
        """Validate a schema definition."""
        pass
    
    @abstractmethod
    async def check_compatibility(self, schema_definition: str, schema_type: SchemaType, 
                                 subject: str, version: Optional[int] = None) -> bool:
        """Check if a schema is compatible with existing versions."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check schema registry health."""
        pass
    
    @abstractmethod
    async def serialize(self, subject: str, data: Any, schema_id: Optional[int] = None) -> bytes:
        """Serialize data using schema."""
        pass
    
    @abstractmethod
    async def deserialize(self, data: bytes, schema_id: int) -> Any:
        """Deserialize data using schema."""
        pass
    
    @abstractmethod
    async def update_compatibility(self, subject: str, compatibility: str) -> bool:
        """Update compatibility level for subject."""
        pass
    
    def close(self) -> None:
        """Close the adapter."""
        pass
