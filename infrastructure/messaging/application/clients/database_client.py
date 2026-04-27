from typing import List, Dict, Any, Optional
from datetime import datetime

from application.clients.base_client import BaseClient, ClientConfig


class DatabaseClient(BaseClient):
    def __init__(self, config: ClientConfig):
        super().__init__(config)
        self.base_path = "/api/v1/database"
    
    def save_event(self, topic: str, partition: int, offset: int, 
                   key: Optional[str] = None, value: Optional[Any] = None,
                   timestamp: Optional[datetime] = None, 
                   headers: Optional[Dict] = None) -> Dict[str, Any]:
        data = {
            "topic": topic,
            "partition": partition,
            "offset": offset,
            "key": key,
            "value": value,
            "timestamp": timestamp.isoformat() if timestamp else None,
            "headers": headers or {}
        }
        return self.post(f"{self.base_path}/events", data)
    
    def save_events_batch(self, events: List[Dict]) -> Dict[str, Any]:
        data = {"events": events}
        return self.post(f"{self.base_path}/events/batch", data)
    
    def get_event(self, event_id: str) -> Dict[str, Any]:
        return self.get(f"{self.base_path}/events/{event_id}")
    
    def get_events_by_topic(self, topic: str, limit: int = 100, 
                           offset: int = 0) -> List[Dict[str, Any]]:
        params = {"topic": topic, "limit": limit, "offset": offset}
        return self.get(f"{self.base_path}/events", params)
    
    def mark_event_processed(self, event_id: str) -> Dict[str, bool]:
        return self.post(f"{self.base_path}/events/{event_id}/processed")
    
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
    
    def delete_events_by_topic(self, topic: str) -> Dict[str, int]:
        return self.delete(f"{self.base_path}/events/{topic}")
    
    def get_event_count(self, topic: Optional[str] = None) -> Dict[str, int]:
        if topic:
            return self.get(f"{self.base_path}/events/{topic}/count")
        return self.get(f"{self.base_path}/events/count")
