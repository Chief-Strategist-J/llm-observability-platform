from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EventRecord:
    topic: str
    partition: int
    offset: int
    key: Optional[str]
    value: Any
    timestamp: datetime
    headers: Optional[Dict[str, Any]] = None
    processed: bool = False
    error: Optional[str] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class ConsumerOffset:
    consumer_group: str
    topic: str
    partition: int
    offset: int
    updated_at: datetime = None

    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


class DatabasePort(ABC):
    @abstractmethod
    def save_event(self, event: EventRecord) -> str:
        pass

    @abstractmethod
    def save_events_batch(self, events: List[EventRecord]) -> List[str]:
        pass

    @abstractmethod
    def get_event(self, event_id: str) -> Optional[EventRecord]:
        pass

    @abstractmethod
    def get_events_by_topic(self, topic: str, limit: int = 100, offset: int = 0) -> List[EventRecord]:
        pass

    @abstractmethod
    def get_unprocessed_events(self, limit: int = 100) -> List[EventRecord]:
        pass

    @abstractmethod
    def mark_event_processed(self, event_id: str, error: Optional[str] = None) -> bool:
        pass

    @abstractmethod
    def save_consumer_offset(self, offset: ConsumerOffset) -> bool:
        pass

    @abstractmethod
    def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> Optional[ConsumerOffset]:
        pass

    @abstractmethod
    def delete_events_by_topic(self, topic: str) -> int:
        pass

    @abstractmethod
    def get_event_count(self, topic: Optional[str] = None) -> int:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
