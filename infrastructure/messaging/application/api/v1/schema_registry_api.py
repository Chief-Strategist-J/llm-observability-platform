from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status, APIRouter
from pydantic import BaseModel, Field

from domain.ports.schema_registry_port import SchemaType
from application.api.v1.validators import Preconditions, Postconditions, ValidationError


class SchemaRegisterRequest(BaseModel):
    subject: str = Field(..., description="Schema subject name")
    schema: str = Field(..., description="Schema definition (AVRO/JSON/PROTOBUF)")
    schema_type: SchemaType = Field(..., description="Schema type (AVRO, PROTOBUF, or JSON)")


class SchemaInfoResponse(BaseModel):
    subject: str
    schema_id: int
    schema_type: str
    schema: str
    version: int
    compatibility: Optional[str] = None


class SchemaCompatibilityRequest(BaseModel):
    subject: str = Field(..., description="Schema subject name")
    schema: str = Field(..., description="Schema definition to check compatibility")
    schema_type: SchemaType = Field(..., description="Schema type")


class CompatibilityUpdateRequest(BaseModel):
    subject: str = Field(..., description="Subject to update compatibility for")
    compatibility: str = Field(..., description="Compatibility level (BACKWARD, FORWARD, FULL, NONE)")


class SerializationRequest(BaseModel):
    subject: str = Field(..., description="Subject for serialization")
    data: Any = Field(..., description="Data to serialize")
    schema_id: Optional[int] = Field(None, description="Optional schema ID to use")


class SerializationResponse(BaseModel):
    data: str
    schema_id: Optional[int] = None


class DeserializationRequest(BaseModel):
    data: str = Field(..., description="Base64-encoded data to deserialize")
    schema_id: int = Field(..., description="Schema ID to use for deserialization")


class DeserializationResponse(BaseModel):
    data: Any
    schema_id: Optional[int] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class SchemaRegistryAPI:
    def __init__(self, schema_registry_port):
        self._schema_registry = schema_registry_port
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        @self.router.post("/schemas", response_model=SchemaInfoResponse)
        def register_schema_route(request: SchemaRegisterRequest):
            return self.register_schema(request)

        @self.router.get("/schemas/{schema_id}", response_model=SchemaInfoResponse)
        def get_schema_route(schema_id: int):
            return self.get_schema(schema_id)

        @self.router.get("/subjects/{subject}/versions/{version}", response_model=SchemaInfoResponse)
        def get_schema_by_subject_route(subject: str, version: int = None):
            return self.get_schema_by_subject(subject, version)

        @self.router.get("/subjects/{subject}/latest", response_model=SchemaInfoResponse)
        def get_latest_schema_route(subject: str):
            return self.get_latest_schema(subject)

        @self.router.get("/subjects")
        def list_subjects_route():
            return self.list_subjects()

        @self.router.get("/subjects/{subject}/versions")
        def list_versions_route(subject: str):
            return self.list_versions(subject)

        @self.router.delete("/subjects/{subject}")
        def delete_subject_route(subject: str):
            return self.delete_subject(subject)

        @self.router.post("/compatibility")
        def check_compatibility_route(request: SchemaCompatibilityRequest):
            return self.check_compatibility(request)

        @self.router.put("/subjects/{subject}/compatibility")
        def update_compatibility_route(request: CompatibilityUpdateRequest):
            return self.update_compatibility(request)

        @self.router.post("/serialize", response_model=SerializationResponse)
        def serialize_route(request: SerializationRequest):
            return self.serialize(request)

        @self.router.post("/deserialize", response_model=DeserializationResponse)
        def deserialize_route(request: DeserializationRequest):
            return self.deserialize(request)

    def register_schema(self, request: SchemaRegisterRequest) -> SchemaInfoResponse:
        try:
            Preconditions.validate_non_empty_string(request.subject, "subject")
            Preconditions.validate_non_empty_string(request.schema, "schema")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            schema_id = self._schema_registry.register_schema(
                request.subject,
                request.schema,
                request.schema_type
            )
            Preconditions.validate_not_none(schema_id, "register_schema")
            schema_info = self._schema_registry.get_schema(schema_id)
            Preconditions.validate_not_none(schema_info, "get_schema")
            return self._build_schema_response(schema_info)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to register schema: {str(e)}"
            )

    def get_schema(self, schema_id: int) -> SchemaInfoResponse:
        try:
            Preconditions.validate_positive(schema_id, "schema_id")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            schema_info = self._schema_registry.get_schema(schema_id)
            if not schema_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Schema with id {schema_id} not found. Verify the schema ID is correct."
                )
            return self._build_schema_response(schema_info)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get schema: {str(e)}"
            )

    def get_schema_by_subject(self, subject: str, version: Optional[int] = None) -> SchemaInfoResponse:
        try:
            Preconditions.validate_non_empty_string(subject, "subject")
            if version is not None:
                Preconditions.validate_positive(version, "version")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            schema_info = self._schema_registry.get_schema_by_subject(subject, version)
            if not schema_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Schema for subject '{subject}' not found. Verify the subject is registered."
                )
            return self._build_schema_response(schema_info)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get schema by subject: {str(e)}"
            )

    def get_latest_schema(self, subject: str) -> SchemaInfoResponse:
        try:
            Preconditions.validate_non_empty_string(subject, "subject")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            schema_info = self._schema_registry.get_latest_schema(subject)
            if not schema_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No schema found for subject '{subject}'. Verify the subject is registered."
                )
            return self._build_schema_response(schema_info)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get latest schema: {str(e)}"
            )

    def list_subjects(self) -> Dict[str, List[str]]:
        try:
            subjects = self._schema_registry.list_subjects()
            return {"subjects": subjects}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list subjects: {str(e)}"
            )

    def list_versions(self, subject: str) -> Dict[str, List[int]]:
        try:
            Preconditions.validate_non_empty_string(subject, "subject")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            versions = self._schema_registry.list_versions(subject)
            return {"subject": subject, "versions": versions}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list versions: {str(e)}"
            )

    def delete_subject(self, subject: str) -> Dict[str, bool]:
        try:
            Preconditions.validate_non_empty_string(subject, "subject")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            success = self._schema_registry.delete_subject(subject)
            Postconditions.validate_success(success, "delete_subject")
            return {"success": True}
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete subject: {str(e)}"
            )

    def check_compatibility(self, request: SchemaCompatibilityRequest) -> Dict[str, bool]:
        try:
            Preconditions.validate_non_empty_string(request.subject, "subject")
            Preconditions.validate_non_empty_string(request.schema, "schema")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            is_compatible = self._schema_registry.check_compatibility(
                request.subject,
                request.schema,
                request.schema_type
            )
            return {"compatible": is_compatible}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to check compatibility: {str(e)}"
            )

    def update_compatibility(self, request: CompatibilityUpdateRequest) -> Dict[str, bool]:
        try:
            Preconditions.validate_non_empty_string(request.subject, "subject")
            Preconditions.validate_non_empty_string(request.compatibility, "compatibility")
            valid_compatibilities = ["BACKWARD", "FORWARD", "FULL", "NONE", "BACKWARD_TRANSITIVE", "FORWARD_TRANSITIVE", "FULL_TRANSITIVE"]
            Preconditions.validate_enum(request.compatibility.upper(), "compatibility", valid_compatibilities)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            success = self._schema_registry.update_compatibility(
                request.subject,
                request.compatibility.upper()
            )
            Postconditions.validate_success(success, "update_compatibility")
            return {"success": True}
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update compatibility: {str(e)}"
            )

    def serialize(self, request: SerializationRequest) -> SerializationResponse:
        try:
            Preconditions.validate_non_empty_string(request.subject, "subject")
            Preconditions.validate_not_none(request.data, "data")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            serialized = self._schema_registry.serialize(
                request.subject,
                request.data,
                request.schema_id
            )
            Preconditions.validate_not_none(serialized, "serialize")
            import base64
            return SerializationResponse(
                data=base64.b64encode(serialized).decode('utf-8'),
                schema_id=request.schema_id
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to serialize data: {str(e)}"
            )

    def deserialize(self, request: DeserializationRequest) -> DeserializationResponse:
        try:
            Preconditions.validate_non_empty_string(request.data, "data")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            import base64
            data_bytes = base64.b64decode(request.data)
            deserialized = self._schema_registry.deserialize(data_bytes, request.schema_id)
            Preconditions.validate_not_none(deserialized, "deserialize")
            return DeserializationResponse(
                data=deserialized,
                schema_id=request.schema_id
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to deserialize data: {str(e)}"
            )

    def _build_schema_response(self, schema_info) -> SchemaInfoResponse:
        return SchemaInfoResponse(
            subject=schema_info.subject,
            schema_id=schema_info.schema_id,
            schema_type=schema_info.schema_type.value if hasattr(schema_info.schema_type, 'value') else str(schema_info.schema_type),
            schema=schema_info.schema,
            version=schema_info.version,
            compatibility=schema_info.compatibility
        )
