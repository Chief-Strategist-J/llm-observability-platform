"""Event processing service."""

from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta

from ...shared.ports.database_port import DatabasePort
from ...shared.types.events import EventRecord, ConsumerOffset


class EventService:
    """Service for processing events with single responsibility for event operations"""
    
    def __init__(self, database: DatabasePort):
        self._database = database

    def _get_event_id(self, event: EventRecord) -> str:
        """Extract event ID from event record"""
        return str(getattr(event, 'id', ""))

    async def process_kafka_record(self, record: Dict[str, Any]) -> str:
        """Process a single Kafka record"""
        event = EventRecord(
            topic=record['topic'],
            partition=record['partition'],
            offset=record['offset'],
            key=str(record['key']) if record.get('key') else None,
            value=record['value'],
            timestamp=datetime.fromtimestamp(record['timestamp'] / 1000) if record.get('timestamp') else datetime.utcnow(),
            headers=record.get('headers')
        )
        return self._database.save_event(event)

    async def process_kafka_records_batch(self, records: List[Dict[str, Any]]) -> List[str]:
        """Process multiple Kafka records in batch"""
        events = [
            EventRecord(
                topic=record['topic'],
                partition=record['partition'],
                offset=record['offset'],
                key=str(record['key']) if record.get('key') else None,
                value=record['value'],
                timestamp=datetime.fromtimestamp(record['timestamp'] / 1000) if record.get('timestamp') else datetime.utcnow(),
                headers=record.get('headers')
            )
            for record in records
        ]
        return self._database.save_events_batch(events)

    async def process_with_custom_logic(self, record: Dict[str, Any], processor: Callable[[Any], Any]) -> Dict[str, Any]:
        """Process record with custom business logic"""
        event_id = await self.process_kafka_record(record)
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
                self._database.mark_event_processed(self._get_event_id(event))
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

    async def get_events_by_topic(self, topic: str, limit: int = 100, offset: int = 0) -> List[EventRecord]:
        """Get events by topic with pagination"""
        return self._database.get_events_by_topic(topic, limit=limit, offset=offset)

    async def get_event_count(self, topic: Optional[str] = None) -> int:
        """Get event count, optionally filtered by topic"""
        return self._database.get_event_count(topic)

    def cleanup_old_events(self, topic: str, days_to_keep: int = 30) -> int:
        """Clean up old events (implementation depends on database adapter)"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        # This would be implemented by specific database adapters
        return self._database.delete_events_by_topic(topic)

    def close(self):
        """Close database connection"""
        self._database.close()
