from abc import ABC, abstractmethod
from domain.ports.database_port import EventRecord


class EventManagementPort(ABC):
    @abstractmethod
    def mark_event_processed(self, event_id: str, error: str = None) -> bool:
        pass

    @abstractmethod
    def delete_events_by_topic(self, topic: str) -> int:
        pass
