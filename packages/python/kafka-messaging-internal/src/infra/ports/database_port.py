"""Database port interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from shared.types.events import EventRecord, ConsumerOffset


class DatabasePort(ABC):
    """Database operations port interface."""
    
    @abstractmethod
    def save_event(self, event: EventRecord) -> str:
        """Save a single event."""
        pass

    @abstractmethod
    def save_events_batch(self, events: List[EventRecord]) -> List[str]:
        """Save multiple events in batch."""
        pass

    @abstractmethod
    def get_event(self, event_id: str) -> Optional[EventRecord]:
        """Get event by ID."""
        pass

    @abstractmethod
    def get_events_by_topic(self, topic: str, limit: int = 100, offset: int = 0) -> List[EventRecord]:
        """Get events by topic with pagination."""
        pass

    @abstractmethod
    def get_unprocessed_events(self, limit: int = 100) -> List[EventRecord]:
        """Get unprocessed events."""
        pass

    @abstractmethod
    def mark_event_processed(self, event_id: str, error: Optional[str] = None) -> bool:
        """Mark event as processed."""
        pass

    @abstractmethod
    def save_consumer_offset(self, offset: ConsumerOffset) -> bool:
        """Save consumer offset."""
        pass

    @abstractmethod
    def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> Optional[ConsumerOffset]:
        """Get consumer offset."""
        pass

    @abstractmethod
    def delete_events_by_topic(self, topic: str) -> int:
        """Delete events by topic."""
        pass

    @abstractmethod
    def get_event_count(self, topic: Optional[str] = None) -> int:
        """Get event count."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close database connection."""
        pass
