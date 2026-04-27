from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from domain.ports.database_port import DatabasePort, EventRecord, ConsumerOffset


class ConsumerRecord:
    def __init__(self, topic: str, partition: int, offset: int, key: Any, value: Any, timestamp: int, headers: Optional[Dict[str, Any]] = None):
        self.topic = topic
        self.partition = partition
        self.offset = offset
        self.key = key
        self.value = value
        self.timestamp = timestamp
        self.headers = headers


class EventHandler:
    def __init__(self, database: DatabasePort):
        self._database = database

    def process_kafka_record(self, record: ConsumerRecord) -> str:
        event = EventRecord(
            topic=record.topic,
            partition=record.partition,
            offset=record.offset,
            key=str(record.key) if record.key else None,
            value=record.value,
            timestamp=datetime.fromtimestamp(record.timestamp / 1000) if record.timestamp else datetime.utcnow(),
            headers=record.headers
        )
        return self._database.save_event(event)

    def process_kafka_records_batch(self, records: List[ConsumerRecord]) -> List[str]:
        events = [
            EventRecord(
                topic=record.topic,
                partition=record.partition,
                offset=record.offset,
                key=str(record.key) if record.key else None,
                value=record.value,
                timestamp=datetime.fromtimestamp(record.timestamp / 1000) if record.timestamp else datetime.utcnow(),
                headers=record.headers
            )
            for record in records
        ]
        return self._database.save_events_batch(events)

    def process_with_custom_logic(self, record: ConsumerRecord, processor: Callable[[Any], Any]) -> Dict[str, Any]:
        event_id = self.process_kafka_record(record)
        try:
            result = processor(record.value)
            self._database.mark_event_processed(event_id)
            return {"event_id": event_id, "success": True, "result": result}
        except Exception as e:
            self._database.mark_event_processed(event_id, error=str(e))
            return {"event_id": event_id, "success": False, "error": str(e)}

    def get_unprocessed_and_process(self, processor: Callable[[EventRecord], Any], batch_size: int = 100) -> List[Dict[str, Any]]:
        events = self._database.get_unprocessed_events(limit=batch_size)
        results = []
        for event in events:
            try:
                result = processor(event)
                self._database.mark_event_processed(str(event_id) if hasattr(event, 'id') else "")
                results.append({"success": True, "result": result})
            except Exception as e:
                results.append({"success": False, "error": str(e)})
        return results

    def save_consumer_offset(self, consumer_group: str, topic: str, partition: int, offset: int) -> bool:
        offset_record = ConsumerOffset(
            consumer_group=consumer_group,
            topic=topic,
            partition=partition,
            offset=offset
        )
        return self._database.save_consumer_offset(offset_record)

    def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> Optional[int]:
        offset_record = self._database.get_consumer_offset(consumer_group, topic, partition)
        return offset_record.offset if offset_record else None

    def get_events_by_topic(self, topic: str, limit: int = 100, offset: int = 0) -> List[EventRecord]:
        return self._database.get_events_by_topic(topic, limit=limit, offset=offset)

    def get_event_count(self, topic: Optional[str] = None) -> int:
        return self._database.get_event_count(topic)

    def cleanup_old_events(self, topic: str, days_to_keep: int = 30) -> int:
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        collection = self._database._events_collection if hasattr(self._database, '_events_collection') else None
        if collection:
            result = collection.delete_many({
                "topic": topic,
                "created_at": {"$lt": cutoff_date}
            })
            return result.deleted_count
        return 0

    def close(self):
        self._database.close()
