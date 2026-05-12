"""Schema-aware event processing service."""

from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

from ...shared.ports.database_port import DatabasePort
from ...shared.ports.schema_registry_port import SchemaRegistryPort
from ...shared.types.events import EventRecord, ConsumerOffset
from ...shared.types.schema import SchemaType


class SchemaAwareEventService:
    """Service for schema-aware event processing with single responsibility for schema operations"""
    
    def __init__(self, database: DatabasePort, schema_registry: SchemaRegistryPort):
        self._database = database
        self._schema_registry = schema_registry
        self._subject_mapping: Dict[str, str] = {}

    def register_subject_mapping(self, topic: str, subject: str):
        """Register mapping between topic and schema subject"""
        self._subject_mapping[topic] = subject

    async def process_kafka_record(self, record: Dict[str, Any], deserialize: bool = True) -> str:
        """Process Kafka record with optional deserialization"""
        value = record['value']
        
        if deserialize and record['topic'] in self._subject_mapping:
            subject = self._subject_mapping[record['topic']]
            if isinstance(value, bytes):
                value = self._schema_registry.deserialize(value)
        
        event = EventRecord(
            topic=record['topic'],
            partition=record['partition'],
            offset=record['offset'],
            key=str(record['key']) if record.get('key') else None,
            value=value,
            timestamp=datetime.fromtimestamp(record['timestamp'] / 1000) if record.get('timestamp') else datetime.utcnow(),
            headers=record.get('headers')
        )
        return self._database.save_event(event)

    async def process_kafka_records_batch(self, records: List[Dict[str, Any]], deserialize: bool = True) -> List[str]:
        """Process multiple Kafka records with optional deserialization"""
        event_ids = []
        for record in records:
            event_id = await self.process_kafka_record(record, deserialize)
            event_ids.append(event_id)
        return event_ids

    def serialize_and_produce(self, topic: str, data: Any, subject: Optional[str] = None) -> bytes:
        """Serialize data for production using schema registry"""
        target_subject = subject or self._subject_mapping.get(topic)
        if target_subject:
            return self._schema_registry.serialize(target_subject, data)
        return str(data).encode('utf-8')

    def register_schema(self, subject: str, schema: str, schema_type: SchemaType) -> int:
        """Register a new schema"""
        return self._schema_registry.register_schema(subject, schema, schema_type)

    def get_schema(self, subject: str, version: Optional[int] = None):
        """Get schema by subject and optional version"""
        return self._schema_registry.get_schema_by_subject(subject, version)

    def check_schema_compatibility(self, subject: str, schema: str, schema_type: SchemaType) -> bool:
        """Check schema compatibility"""
        return self._schema_registry.check_compatibility(subject, schema, schema_type)

    async def process_with_custom_logic(self, record: Dict[str, Any], processor: Callable[[Any], Any], deserialize: bool = True) -> Dict[str, Any]:
        """Process record with custom business logic and optional deserialization"""
        event_id = await self.process_kafka_record(record, deserialize)
        try:
            result = processor(record['value'])
            self._database.mark_event_processed(event_id)
            return {"event_id": event_id, "success": True, "result": result}
        except Exception as e:
            self._database.mark_event_processed(event_id, error=str(e))
            return {"event_id": event_id, "success": False, "error": str(e)}

    async def get_unprocessed_and_process(self, processor: Callable[[EventRecord], Any], batch_size: int = 100) -> List[Dict[str, Any]]:
        """Get unprocessed events and process them"""
        events = self._database.get_unprocessed_events(limit=batch_size)
        results = []
        for event in events:
            try:
                result = processor(event)
                event_id = getattr(event, 'id', None)
                if event_id:
                    self._database.mark_event_processed(str(event_id))
                results.append({"success": True, "result": result})
            except Exception as e:
                results.append({"success": False, "error": str(e)})
        return results

    async def save_consumer_offset(self, consumer_group: str, topic: str, partition: int, offset: int) -> bool:
        """Save consumer offset"""
        offset_record = ConsumerOffset(
            consumer_group=consumer_group,
            topic=topic,
            partition=partition,
            offset=offset
        )
        return self._database.save_consumer_offset(offset_record)

    async def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> Optional[int]:
        """Get consumer offset"""
        offset_record = self._database.get_consumer_offset(consumer_group, topic, partition)
        return offset_record.offset if offset_record else None

    def list_registered_subjects(self) -> List[str]:
        """List all registered subjects"""
        return self._schema_registry.list_subjects()

    def close(self):
        """Close connections"""
        self._database.close()
        self._schema_registry.close()
