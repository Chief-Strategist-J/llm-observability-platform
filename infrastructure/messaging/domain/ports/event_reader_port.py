from abc import ABC, abstractmethod
from typing import List, Optional
from domain.ports.database_port import EventRecord


class EventReaderPort(ABC):
    @abstractmethod
    def get_event(self, event_id: str) -> Optional[EventRecord]:
        pass

    @abstractmethod
    def get_events_by_topic(self, topic: str, limit: int = 100, offset: int = 0) -> List[EventRecord]:
        pass

    @abstractmethod
    def get_unprocessed_events(self, limit: int = 100) -> List[EventRecord]:
        pass
