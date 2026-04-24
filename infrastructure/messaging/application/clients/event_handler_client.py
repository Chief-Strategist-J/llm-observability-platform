from typing import List, Dict, Any, Optional

from infrastructure.messaging.application.clients.base_client import BaseClient, ClientConfig


class EventHandlerClient(BaseClient):
    def __init__(self, config: ClientConfig):
        super().__init__(config)
        self.base_path = "/api/v1/event-handler"
    
    def process_record(self, topic: str, partition: int, offset: int,
                       key: Optional[str] = None, value: Optional[Any] = None,
                       timestamp: int = 0, headers: Optional[Dict] = None) -> Dict[str, Any]:
        data = {
            "topic": topic,
            "partition": partition,
            "offset": offset,
            "key": key,
            "value": value,
            "timestamp": timestamp,
            "headers": headers or {}
        }
        return self.post(f"{self.base_path}/process-record", data)
    
    def process_records_batch(self, records: List[Dict]) -> Dict[str, Any]:
        data = {"records": records}
        return self.post(f"{self.base_path}/process-records-batch", data)
    
    def save_consumer_offset(self, consumer_group: str, topic: str,
                            partition: int, offset: int) -> Dict[str, bool]:
        data = {
            "consumer_group": consumer_group,
            "topic": topic,
            "partition": partition,
            "offset": offset
        }
        return self.post(f"{self.base_path}/consumer-offsets", data)
    
    def get_consumer_offset(self, consumer_group: str, topic: str,
                           partition: int) -> Dict[str, Any]:
        return self.get(f"{self.base_path}/consumer-offsets/{consumer_group}/{topic}/{partition}")
    
    def get_events_by_topic(self, topic: str, limit: int = 100,
                           offset: int = 0) -> List[Dict[str, Any]]:
        params = {"topic": topic, "limit": limit, "offset": offset}
        return self.get(f"{self.base_path}/events", params)
    
    def get_event_count(self, topic: Optional[str] = None) -> Dict[str, int]:
        if topic:
            return self.get(f"{self.base_path}/events/{topic}/count")
        return self.get(f"{self.base_path}/events/count")


class SchemaAwareEventHandlerClient(BaseClient):
    def __init__(self, config: ClientConfig):
        super().__init__(config)
        self.base_path = "/api/v1/schema-aware-event-handler"
    
    def register_subject_mapping(self, topic: str, subject: str) -> Dict[str, bool]:
        data = {"topic": topic, "subject": subject}
        return self.post(f"{self.base_path}/register-subject-mapping", data)
    
    def process_record(self, topic: str, partition: int, offset: int,
                       key: Optional[str] = None, value: Optional[Any] = None,
                       timestamp: int = 0, headers: Optional[Dict] = None,
                       deserialize: bool = True) -> Dict[str, Any]:
        data = {
            "topic": topic,
            "partition": partition,
            "offset": offset,
            "key": key,
            "value": value,
            "timestamp": timestamp,
            "headers": headers or {}
        }
        params = {"deserialize": deserialize}
        return self.post(f"{self.base_path}/process-record", data, params)
    
    def process_records_batch(self, records: List[Dict],
                             deserialize: bool = True) -> Dict[str, Any]:
        data = {"records": records}
        params = {"deserialize": deserialize}
        return self.post(f"{self.base_path}/process-records-batch", data, params)
    
    def serialize_and_produce(self, topic: str, data: Dict,
                              subject: Optional[str] = None,
                              schema_id: Optional[int] = None,
                              partition: Optional[int] = None,
                              key: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "topic": topic,
            "data": data
        }
        if subject:
            payload["subject"] = subject
        if schema_id:
            payload["schema_id"] = schema_id
        if partition is not None:
            payload["partition"] = partition
        if key:
            payload["key"] = key
        return self.post(f"{self.base_path}/serialize-and-produce", payload)
    
    def save_consumer_offset(self, consumer_group: str, topic: str,
                            partition: int, offset: int) -> Dict[str, bool]:
        data = {
            "consumer_group": consumer_group,
            "topic": topic,
            "partition": partition,
            "offset": offset
        }
        return self.post(f"{self.base_path}/consumer-offsets", data)
    
    def get_consumer_offset(self, consumer_group: str, topic: str,
                           partition: int) -> Dict[str, Any]:
        return self.get(f"{self.base_path}/consumer-offsets/{consumer_group}/{topic}/{partition}")
    
    def list_registered_subjects(self) -> Dict[str, List[str]]:
        return self.get(f"{self.base_path}/registered-subjects")
