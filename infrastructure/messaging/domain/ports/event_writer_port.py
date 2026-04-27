from abc import ABC, abstractmethod
from typing import List
from domain.ports.database_port import EventRecord


class EventWriterPort(ABC):
    @abstractmethod
    def save_event(self, event: EventRecord) -> str:
        pass

    @abstractmethod
    def save_events_batch(self, events: List[EventRecord]) -> List[str]:
        pass
