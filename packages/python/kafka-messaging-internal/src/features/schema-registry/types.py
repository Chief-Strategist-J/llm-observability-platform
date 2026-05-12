"""Type definitions for schema registry feature."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class SchemaTypeEnum(str, Enum):
    """Supported schema types."""
    AVRO = "AVRO"
    JSON = "JSON"
    PROTOBUF = "PROTOBUF"


class CompatibilityLevelEnum(str, Enum):
    """Supported compatibility levels."""
    BACKWARD = "BACKWARD"
    FORWARD = "FORWARD"
    FULL = "FULL"
    NONE = "NONE"


class SchemaRegisterRequest(BaseModel):
    """Request model for schema registration."""
    subject: str = Field(..., min_length=1, max_length=255, description="Schema subject name")
    schema: str = Field(..., min_length=1, description="Schema definition")
    schema_type: SchemaTypeEnum = Field(..., description="Schema type")


class SchemaInfoResponse(BaseModel):
    """Response model for schema information."""
    subject: str = Field(..., description="Schema subject name")
    schema_id: int = Field(..., description="Schema ID")
    schema_type: str = Field(..., description="Schema type")
    schema: str = Field(..., description="Schema definition")
    version: int = Field(..., description="Schema version")
    compatibility: Optional[str] = Field(None, description="Compatibility level")


class SchemaCompatibilityRequest(BaseModel):
    """Request model for schema compatibility check."""
    subject: str = Field(..., min_length=1, max_length=255, description="Schema subject name")
    schema: str = Field(..., min_length=1, description="Schema definition to check")
    schema_type: SchemaTypeEnum = Field(..., description="Schema type")


class SchemaCompatibilityResponse(BaseModel):
    """Response model for schema compatibility check."""
    is_compatible: bool = Field(..., description="Whether schema is compatible")
    compatibility_level: Optional[str] = Field(None, description="Detected compatibility level")
    message: str = Field(..., description="Compatibility check result message")
    subject: str = Field(..., description="Schema subject name")


class CompatibilityUpdateRequest(BaseModel):
    """Request model for compatibility level update."""
    subject: str = Field(..., min_length=1, max_length=255, description="Subject to update")
    compatibility: CompatibilityLevelEnum = Field(..., description="New compatibility level")


class CompatibilityUpdateResponse(BaseModel):
    """Response model for compatibility level update."""
    subject: str = Field(..., description="Updated subject name")
    compatibility: str = Field(..., description="Updated compatibility level")
    message: str = Field(..., description="Update result message")


class SerializationRequest(BaseModel):
    """Request model for data serialization."""
    subject: str = Field(..., min_length=1, max_length=255, description="Schema subject")
    data: Any = Field(..., description="Data to serialize")
    schema_id: Optional[int] = Field(None, description="Optional schema ID to use")


class SerializationResponse(BaseModel):
    """Response model for data serialization."""
    data: str = Field(..., description="Serialized data (base64 encoded)")
    schema_id: Optional[int] = Field(None, description="Schema ID used")
    subject: str = Field(..., description="Schema subject used")


class DeserializationRequest(BaseModel):
    """Request model for data deserialization."""
    data: str = Field(..., description="Base64-encoded data to deserialize")
    schema_id: int = Field(..., description="Schema ID to use")


class DeserializationResponse(BaseModel):
    """Response model for data deserialization."""
    data: Any = Field(..., description="Deserialized data")
    schema_id: int = Field(..., description="Schema ID used")


class SubjectsListResponse(BaseModel):
    """Response model for subjects list."""
    subjects: List[str] = Field(..., description="List of schema subjects")


class SchemaRegisterResponse(BaseModel):
    """Response model for schema registration."""
    schema_id: int = Field(..., description="Registered schema ID")
    subject: str = Field(..., description="Schema subject name")
    version: int = Field(..., description="Schema version")
    duplicate: bool = Field(False, description="Whether schema was duplicate")
