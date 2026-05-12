"""Public interface for database operations feature."""

from typing import Any, Dict, List, Optional
from opentelemetry import trace
from .service import DatabaseOperationsService
from kafka_messaging_internal.shared.di.container import get_container
from kafka_messaging_internal.shared.ports.database_port import DatabasePort
from kafka_messaging_internal.shared.errors.exceptions import ValidationError


class DatabaseOperations:
    """Database operations feature entry point following SRP rules."""
    
    def __init__(self):
        self.tracer = trace.get_tracer(__name__)
        self.container = get_container()
        
        with self.tracer.start_as_current_span("database_operations_initialization") as span:
            span.set_attributes({
                "service.name": "kafka-messaging-internal",
                "feature.name": "database_operations",
                "api.version": "v1"
            })
            
            try:
                self.database = self.container.get(DatabasePort)
                self.service = DatabaseOperationsService(self.database)
                
                span.set_status(trace.Status(trace.StatusCode.OK))
                
            except Exception as e:
                span.record_error(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
    
    async def get_event_count(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get event count with optional filters."""
        return await self.service.get_event_count(filters)
    
    async def delete_events_by_topic(self, topic: str) -> Dict[str, Any]:
        """Delete events by topic."""
        return await self.service.delete_events_by_topic(topic)
    
    async def get_unprocessed_events(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get unprocessed events."""
        return await self.service.get_unprocessed_events(filters)


# Factory function for DI container
def create_database_operations() -> DatabaseOperations:
    """Create database operations feature instance."""
    return DatabaseOperations()
