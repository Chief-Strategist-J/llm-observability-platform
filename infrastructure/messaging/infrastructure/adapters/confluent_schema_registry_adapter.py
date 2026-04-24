import json
from typing import Any, Dict, List, Optional
import requests
from confluent_kafka.schema_registry import SchemaRegistryClient as ConfluentSchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
from confluent_kafka.schema_registry.json_schema import JsonSchemaSerializer, JsonSchemaDeserializer
from infrastructure.messaging.domain.ports.schema_registry_port import SchemaRegistryPort, SchemaInfo, SchemaType


class ConfluentSchemaRegistryAdapter(SchemaRegistryPort):
    def __init__(self, url: str, auth: Optional[Dict[str, str]] = None):
        conf = {"url": url}
        if auth:
            conf.update(auth)
        self._client = ConfluentSchemaRegistryClient(conf)
        self._base_url = url

    def register_schema(self, subject: str, schema: str, schema_type: SchemaType) -> int:
        schema_str = json.dumps({"schema": schema}) if schema_type == SchemaType.AVRO else schema
        schema_id = self._client.register_schema(subject, schema_str)
        return schema_id

    def get_schema(self, schema_id: int) -> SchemaInfo:
        schema = self._client.get_schema(schema_id)
        return SchemaInfo(
            subject=schema.subject,
            schema_id=schema.schema_id,
            schema_type=SchemaType(schema.schema_type),
            schema=schema.schema_str,
            version=schema.version
        )

    def get_schema_by_subject(self, subject: str, version: Optional[int] = None) -> SchemaInfo:
        if version:
            schema = self._client.get_schema(subject, version)
        else:
            schema = self._client.get_latest_version(subject)
        return SchemaInfo(
            subject=schema.subject,
            schema_id=schema.schema_id,
            schema_type=SchemaType(schema.schema_type),
            schema=schema.schema_str,
            version=schema.version
        )

    def get_latest_schema(self, subject: str) -> SchemaInfo:
        schema = self._client.get_latest_version(subject)
        return SchemaInfo(
            subject=schema.subject,
            schema_id=schema.schema_id,
            schema_type=SchemaType(schema.schema_type),
            schema=schema.schema_str,
            version=schema.version
        )

    def list_subjects(self) -> List[str]:
        return self._client.get_subjects()

    def list_versions(self, subject: str) -> List[int]:
        return self._client.get_subject_versions(subject)

    def delete_subject(self, subject: str) -> bool:
        try:
            self._client.delete_subject(subject)
            return True
        except Exception:
            return False

    def check_compatibility(self, subject: str, schema: str, schema_type: SchemaType) -> bool:
        try:
            is_compatible = self._client.check_compatibility(subject, schema, schema_type.value.lower())
            return is_compatible
        except Exception:
            return False

    def update_compatibility(self, subject: str, compatibility: str) -> bool:
        try:
            self._client.update_compatibility(subject, compatibility)
            return True
        except Exception:
            return False

    def serialize(self, subject: str, data: Any, schema_id: Optional[int] = None) -> bytes:
        schema_info = self.get_schema_by_subject(subject)
        
        if schema_info.schema_type == SchemaType.AVRO:
            serializer = AvroSerializer(schema_info.schema, self._client)
            return serializer(data, None)
        elif schema_info.schema_type == SchemaType.JSON:
            serializer = JsonSchemaSerializer(schema_info.schema, self._client)
            return serializer(data, None)
        else:
            return json.dumps(data).encode('utf-8')

    def deserialize(self, data: bytes, schema_id: Optional[int] = None) -> Any:
        if schema_id:
            schema_info = self.get_schema(schema_id)
        else:
            return json.loads(data.decode('utf-8'))
        
        if schema_info.schema_type == SchemaType.AVRO:
            deserializer = AvroDeserializer(schema_info.schema, self._client)
            return deserializer(data, None)
        elif schema_info.schema_type == SchemaType.JSON:
            deserializer = JsonSchemaDeserializer(schema_info.schema, self._client)
            return deserializer(data, None)
        else:
            return json.loads(data.decode('utf-8'))

    def close(self) -> None:
        pass
