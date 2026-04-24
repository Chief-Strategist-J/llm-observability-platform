from typing import List, Optional
from datetime import datetime

from infrastructure.messaging.domain.ports.database_port import DatabasePort, EventRecord, ConsumerOffset


class DatabaseDomainClient:
    def __init__(self, database_port: DatabasePort):
        self._database = database_port
    
    def save_event(self, topic: str, partition: int, offset: int,
                   key: Optional[str] = None, value: Optional[str] = None,
                   timestamp: Optional[datetime] = None,
                   headers: Optional[dict] = None) -> str:
        event = EventRecord(
            topic=topic,
            partition=partition,
            offset=offset,
            key=key,
            value=value,
            timestamp=timestamp or datetime.utcnow(),
            headers=headers or {}
        )
        return self._database.save_event(event)
    
    def save_events_batch(self, events: List[dict]) -> List[str]:
        event_records = [
            EventRecord(
                topic=e["topic"],
                partition=e["partition"],
                offset=e["offset"],
                key=e.get("key"),
                value=e.get("value"),
                timestamp=e.get("timestamp") or datetime.utcnow(),
                headers=e.get("headers", {})
            )
            for e in events
        ]
        return self._database.save_events_batch(event_records)
    
    def get_event(self, event_id: str) -> EventRecord:
        return self._database.get_event(event_id)
    
    def get_events_by_topic(self, topic: str, limit: int = 100,
                           offset: int = 0) -> List[EventRecord]:
        return self._database.get_events_by_topic(topic, limit, offset)
    
    def get_unprocessed_events(self, limit: int = 100) -> List[EventRecord]:
        return self._database.get_unprocessed_events(limit)
    
    def mark_event_processed(self, event_id: str) -> bool:
        return self._database.mark_event_processed(event_id)
    
    def save_consumer_offset(self, consumer_group: str, topic: str,
                            partition: int, offset: int) -> bool:
        offset_obj = ConsumerOffset(
            consumer_group=consumer_group,
            topic=topic,
            partition=partition,
            offset=offset
        )
        return self._database.save_consumer_offset(offset_obj)
    
    def get_consumer_offset(self, consumer_group: str, topic: str,
                           partition: int) -> Optional[ConsumerOffset]:
        return self._database.get_consumer_offset(consumer_group, topic, partition)
    
    def delete_events_by_topic(self, topic: str) -> int:
        return self._database.delete_events_by_topic(topic)
    
    def get_event_count(self, topic: Optional[str] = None) -> int:
        return self._database.get_event_count(topic)
    
    def close(self):
        if hasattr(self._database, 'close'):
            self._database.close()
