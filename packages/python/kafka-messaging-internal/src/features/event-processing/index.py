"""Public interface for event processing feature."""

from typing import Any, Dict, List, Optional
from .service import EventProcessingService
from ...shared.di.container import get_container
from ...shared.ports.database_port import DatabasePort


class EventProcessing:
    """Event processing feature entry point following SRP rules."""
    
    def __init__(self):
        self.container = get_container()
        self.database = self.container.get(DatabasePort)
        self.service = EventProcessingService(self.database)
    
    def process_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single event."""
        return self.service.process_event(event_data)
    
    def process_events_batch(self, events_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process multiple events in batch."""
        return self.service.process_events_batch(events_data)
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get event by ID."""
        return self.service.get_event(event_id)
    
    def query_events(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Query events with filters."""
        return self.service.query_events(filters)
    
    def update_consumer_offset(self, offset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update consumer offset."""
        return self.service.update_consumer_offset(offset_data)
    
    def get_consumer_offsets(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get consumer offsets."""
        return self.service.get_consumer_offsets(filters)


# Factory function for DI container
def create_event_processing() -> EventProcessing:
    """Create event processing feature instance."""
    return EventProcessing()
