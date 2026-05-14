"""Database port interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DatabaseConfig:
    """Database configuration."""
    dsn: str
    pool_size: int = 10
    max_overflow: int = 20


@dataclass
class EventRecord:
    """Event record data structure."""
    event_id: Optional[str] = None
    topic: str = ""
    partition: int = 0
    offset: int = 0
    key: Optional[str] = None
    value: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    headers: Optional[Dict[str, Any]] = None
    processed: bool = False
    error: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class ConsumerOffset:
    """Consumer offset data structure."""
    consumer_group: str = ""
    topic: str = ""
    partition: int = 0
    offset: int = 0
    updated_at: Optional[datetime] = None


class DatabasePort(ABC):
    """Database interface following hexagonal architecture."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""
        pass
    
    @abstractmethod
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results."""
        pass
    
    @abstractmethod
    async def execute_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Execute a command and return affected rows."""
        pass
    
    @abstractmethod
    async def begin_transaction(self) -> None:
        """Begin a transaction."""
        pass
    
    @abstractmethod
    async def commit_transaction(self) -> None:
        """Commit a transaction."""
        pass
    
    @abstractmethod
    async def rollback_transaction(self) -> None:
        """Rollback a transaction."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check database health."""
        pass
    
    @abstractmethod
    async def save_event(self, event: EventRecord) -> str:
        """Save an event and return its ID."""
        pass
    
    @abstractmethod
    async def mark_event_processed(self, event_id: str, error: Optional[str] = None) -> bool:
        """Mark an event as processed, optionally with error."""
        pass
    
    @abstractmethod
    async def save_consumer_offset(self, offset: ConsumerOffset) -> bool:
        """Save consumer offset."""
        pass

    @abstractmethod
    async def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> Optional[ConsumerOffset]:
        """Get consumer offset."""
        pass

    @abstractmethod
    async def get_events_by_topic(self, topic: str, limit: int = 100, offset: int = 0) -> List[EventRecord]:
        """Get events by topic with pagination."""
        pass

    @abstractmethod
    async def get_unprocessed_events(self, limit: int = 100) -> List[EventRecord]:
        """Get unprocessed events."""
        pass

    @abstractmethod
    async def get_event_count(self, topic: Optional[str] = None) -> int:
        """Get event count with optional filters."""
        pass

    @abstractmethod
    async def save_events_batch(self, events: List[EventRecord]) -> List[str]:
        """Save events in batch and return their IDs."""
        pass

    @abstractmethod
    async def delete_events_by_topic(self, topic: str) -> int:
        """Delete events by topic and return count."""
        pass

    @abstractmethod
    async def get_event(self, event_id: str) -> Optional[EventRecord]:
        """Get event by ID."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close database connections."""
        pass
