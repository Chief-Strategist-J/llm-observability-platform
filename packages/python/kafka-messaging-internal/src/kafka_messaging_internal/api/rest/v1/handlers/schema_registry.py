"""Schema Registry API handlers following OpenAPI contract."""

from typing import Any, List, Optional, Dict
from fastapi import HTTPException, status, APIRouter, Query
from pydantic import BaseModel, Field

from kafka_messaging_internal.shared.ports.schema_registry_port import SchemaRegistryPort
from kafka_messaging_internal.shared.types.schema import SchemaInfo, SchemaType


class SchemaRegisterRequest(BaseModel):
    """Request model for registering a schema"""
    subject: str = Field(..., description="Schema subject name")
    schema_definition: str = Field(..., description="Schema definition (AVRO/JSON/PROTOBUF)")
    schema_type: SchemaType = Field(..., description="Schema type")


class SchemaCompatibilityRequest(BaseModel):
    """Request model for checking schema compatibility"""
    subject: str = Field(..., description="Schema subject name")
    schema_definition: str = Field(..., description="Schema definition to check compatibility")
    schema_type: SchemaType = Field(..., description="Schema type")


class CompatibilityUpdateRequest(BaseModel):
    """Request model for updating compatibility level"""
    subject: str = Field(..., description="Subject to update compatibility for")
    compatibility: str = Field(..., description="Compatibility level (BACKWARD/FORWARD/FULL/NONE)")


class SerializationRequest(BaseModel):
    """Request model for serializing data"""
    subject: str = Field(..., description="Subject for serialization")
    data: Any = Field(..., description="Data to serialize")
    schema_id: Optional[int] = Field(None, description="Optional schema ID to use")


class DeserializationRequest(BaseModel):
    """Request model for deserializing data"""
    data: str = Field(..., description="Base64-encoded data to deserialize")
    schema_id: int = Field(..., description="Schema ID to use for deserialization")


class SchemaRegistryAPI:
    """REST API handlers for schema registry operations"""
    
    def __init__(self, schema_registry: SchemaRegistryPort):
        self._schema_registry = schema_registry
        self.router = APIRouter()

    def _setup_routes(self):
        """Setup API routes"""
        
        @self.router.post("/schemas", status_code=status.HTTP_201_CREATED)
        async def register_schema(request: SchemaRegisterRequest) -> Dict[str, Any]:
            """Register a new schema"""
            try:
                schema_id = self._schema_registry.register_schema(
                    request.subject, request.schema_definition, request.schema_type
                )
                return {
                    "schema_id": schema_id,
                    "subject": request.subject,
                    "version": 1,  # Simplified - real implementation would get version
                    "success": True
                }
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.get("/schemas")
        async def list_subjects() -> Dict[str, Any]:
            """List all schema subjects"""
            try:
                subjects = self._schema_registry.list_subjects()
                return {"subjects": subjects}
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.get("/schemas/{subject}")
        async def get_schema_by_subject(
            subject: str,
            version: Optional[int] = Query(None, description="Specific version to retrieve")
        ) -> Dict[str, Any]:
            """Get schema by subject"""
            try:
                schema_info = self._schema_registry.get_schema_by_subject(subject, version)
                return {
                    "subject": schema_info.subject,
                    "schema_id": schema_info.schema_id,
                    "schema_type": schema_info.schema_type.value,
                    "schema": schema_info.schema,
                    "version": schema_info.version,
                    "compatibility": schema_info.compatibility
                }
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Schema not found"
                )

        @self.router.post("/compatibility")
        async def check_compatibility(request: SchemaCompatibilityRequest) -> Dict[str, Any]:
            """Check schema compatibility"""
            try:
                is_compatible = self._schema_registry.check_compatibility(
                    request.subject, request.schema_definition, request.schema_type
                )
                return {
                    "is_compatible": is_compatible,
                    "compatibility_level": "BACKWARD",  # Simplified
                    "message": "Schema is compatible" if is_compatible else "Schema is not compatible"
                }
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.put("/compatibility/{subject}")
        async def update_compatibility(
            subject: str,
            request: CompatibilityUpdateRequest
        ) -> Dict[str, Any]:
            """Update compatibility level for a subject"""
            try:
                success = self._schema_registry.update_compatibility(
                    subject, request.compatibility
                )
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Subject not found"
                    )
                return {
                    "subject": subject,
                    "compatibility": request.compatibility,
                    "success": True
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.post("/serialize")
        async def serialize_data(request: SerializationRequest) -> Dict[str, Any]:
            """Serialize data using schema"""
            try:
                serialized_data = self._schema_registry.serialize(
                    request.subject, request.data, request.schema_id
                )
                import base64
                return {
                    "data": base64.b64encode(serialized_data).decode('utf-8'),
                    "schema_id": request.schema_id
                }
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.post("/deserialize")
        async def deserialize_data(request: DeserializationRequest) -> Dict[str, Any]:
            """Deserialize data using schema"""
            try:
                import base64
                data_bytes = base64.b64decode(request.data)
                deserialized_data = self._schema_registry.deserialize(data_bytes, request.schema_id)
                return {
                    "data": deserialized_data,
                    "schema_id": request.schema_id
                }
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

    def get_router(self) -> APIRouter:
        """Get configured router"""
        self._setup_routes()
        return self.router
