"""Public interface for database operations feature."""

from typing import Any, Dict, List, Optional
from .service import DatabaseOperationsService
from ...shared.di.container import get_container
from ...shared.ports.database_port import DatabasePort


class DatabaseOperations:
    """Database operations feature entry point following SRP rules."""
    
    def __init__(self):
        self.container = get_container()
        self.database = self.container.get(DatabasePort)
        self.service = DatabaseOperationsService(self.database)
    
    def get_event_count(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get event count with optional topic filter."""
        return self.service.get_event_count(filters)
    
    def delete_events_by_topic(self, topic: str) -> Dict[str, Any]:
        """Delete events by topic."""
        return self.service.delete_events_by_topic(topic)
    
    def get_unprocessed_events(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get unprocessed events."""
        return self.service.get_unprocessed_events(filters)


# Factory function for DI container
def create_database_operations() -> DatabaseOperations:
    """Create database operations feature instance."""
    return DatabaseOperations()
