"""Persistence strategy port interface."""

from abc import ABC, abstractmethod
from typing import List

from shared.types.events import EventRecord


class PersistenceStrategyPort(ABC):
    """Port interface for persistence strategies"""
    
    @abstractmethod
    async def save(self, event: EventRecord) -> str:
        """Save a single event"""
        pass
    
    @abstractmethod
    async def save_batch(self, events: List[EventRecord]) -> List[str]:
        """Save multiple events in batch"""
        pass
