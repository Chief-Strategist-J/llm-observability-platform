from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum


class SchemaType(str, Enum):
    AVRO = "AVRO"
    PROTOBUF = "PROTOBUF"
    JSON = "JSON"


class SchemaInfo:
    def __init__(
        self,
        subject: str,
        schema_id: int,
        schema_type: SchemaType,
        schema: str,
        version: int,
        compatibility: Optional[str] = None
    ):
        self.subject = subject
        self.schema_id = schema_id
        self.schema_type = schema_type
        self.schema = schema
        self.version = version
        self.compatibility = compatibility


class SchemaRegistryPort(ABC):
    @abstractmethod
    def register_schema(self, subject: str, schema: str, schema_type: SchemaType) -> int:
        pass

    @abstractmethod
    def get_schema(self, schema_id: int) -> SchemaInfo:
        pass

    @abstractmethod
    def get_schema_by_subject(self, subject: str, version: Optional[int] = None) -> SchemaInfo:
        pass

    @abstractmethod
    def get_latest_schema(self, subject: str) -> SchemaInfo:
        pass

    @abstractmethod
    def list_subjects(self) -> List[str]:
        pass

    @abstractmethod
    def list_versions(self, subject: str) -> List[int]:
        pass

    @abstractmethod
    def delete_subject(self, subject: str) -> bool:
        pass

    @abstractmethod
    def check_compatibility(self, subject: str, schema: str, schema_type: SchemaType) -> bool:
        pass

    @abstractmethod
    def update_compatibility(self, subject: str, compatibility: str) -> bool:
        pass

    @abstractmethod
    def serialize(self, subject: str, data: Any, schema_id: Optional[int] = None) -> bytes:
        pass

    @abstractmethod
    def deserialize(self, data: bytes, schema_id: Optional[int] = None) -> Any:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
