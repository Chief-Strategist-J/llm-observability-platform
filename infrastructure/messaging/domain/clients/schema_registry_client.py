from typing import List, Optional

from domain.ports.schema_registry_port import SchemaRegistryPort, SchemaType, SchemaInfo


class SchemaRegistryDomainClient:
    def __init__(self, schema_registry_port: SchemaRegistryPort):
        self._schema_registry = schema_registry_port
    
    def register_schema(self, subject: str, schema: str,
                        schema_type: SchemaType = SchemaType.AVRO) -> int:
        return self._schema_registry.register_schema(subject, schema, schema_type)
    
    def get_schema(self, schema_id: int) -> SchemaInfo:
        return self._schema_registry.get_schema(schema_id)
    
    def get_schema_by_subject(self, subject: str,
                             version: Optional[int] = None) -> SchemaInfo:
        return self._schema_registry.get_schema_by_subject(subject, version)
    
    def get_latest_schema(self, subject: str) -> SchemaInfo:
        return self._schema_registry.get_latest_schema(subject)
    
    def list_subjects(self) -> List[str]:
        return self._schema_registry.list_subjects()
    
    def list_versions(self, subject: str) -> List[int]:
        return self._schema_registry.list_versions(subject)
    
    def delete_subject(self, subject: str) -> bool:
        return self._schema_registry.delete_subject(subject)
    
    def check_compatibility(self, subject: str, schema: str,
                           schema_type: SchemaType = SchemaType.AVRO) -> bool:
        return self._schema_registry.check_compatibility(subject, schema, schema_type)
    
    def update_compatibility(self, subject: str, compatibility: str) -> bool:
        return self._schema_registry.update_compatibility(subject, compatibility)
    
    def serialize(self, subject: str, data: dict,
                  schema_id: Optional[int] = None) -> bytes:
        return self._schema_registry.serialize(subject, data, schema_id)
    
    def deserialize(self, data: bytes, schema_id: int) -> dict:
        return self._schema_registry.deserialize(data, schema_id)
    
    def close(self):
        close_method = getattr(self._schema_registry, 'close', None)
        if close_method:
            close_method()
