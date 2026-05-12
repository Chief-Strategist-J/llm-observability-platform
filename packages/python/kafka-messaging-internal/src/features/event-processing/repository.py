"""Repository layer for event processing - uses port interfaces only."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from opentelemetry import trace
from ...shared.ports.database_port import DatabasePort, EventRecord, ConsumerOffset


class EventRepository:
    """Repository for event operations using DatabasePort interface only."""
    
    def __init__(self, database: DatabasePort):
        self.database = database
        self.tracer = trace.get_tracer(__name__)
    
    def save_event(self, event: EventRecord) -> str:
        """Save event using database port."""
        with self.tracer.start_as_current_span("event_repository.save_event") as span:
            span.set_attribute("feature.name", "event-processing")
            span.set_attribute("operation", "repository_save")
            return self.database.save_event(event)
    
    def save_events_batch(self, events: List[EventRecord]) -> List[str]:
        """Save events batch using database port."""
        with self.tracer.start_as_current_span("event_repository.save_events_batch") as span:
            span.set_attribute("feature.name", "event-processing")
            span.set_attribute("operation", "repository_save_batch")
            return self.database.save_events_batch(events)
    
    def get_event(self, event_id: str) -> Optional[EventRecord]:
        """Get event using database port."""
        with self.tracer.start_as_current_span("event_repository.get_event") as span:
            span.set_attribute("feature.name", "event-processing")
            span.set_attribute("operation", "repository_get")
            return self.database.get_event(event_id)
    
    def get_events_by_topic(self, topic: str, limit: int = 100, offset: int = 0) -> List[EventRecord]:
        """Get events by topic using database port."""
        with self.tracer.start_as_current_span("event_repository.get_events_by_topic") as span:
            span.set_attribute("feature.name", "event-processing")
            span.set_attribute("operation", "repository_query")
            return self.database.get_events_by_topic(topic, limit, offset)
    
    def mark_event_processed(self, event_id: str, error: Optional[str] = None) -> bool:
        """Mark event as processed using database port."""
        with self.tracer.start_as_current_span("event_repository.mark_event_processed") as span:
            span.set_attribute("feature.name", "event-processing")
            span.set_attribute("operation", "repository_update")
            return self.database.mark_event_processed(event_id, error)
    
    def save_consumer_offset(self, offset: ConsumerOffset) -> bool:
        """Save consumer offset using database port."""
        with self.tracer.start_as_current_span("event_repository.save_consumer_offset") as span:
            span.set_attribute("feature.name", "event-processing")
            span.set_attribute("operation", "repository_save")
            return self.database.save_consumer_offset(offset)
    
    def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> Optional[ConsumerOffset]:
        """Get consumer offset using database port."""
        with self.tracer.start_as_current_span("event_repository.get_consumer_offset") as span:
            span.set_attribute("feature.name", "event-processing")
            span.set_attribute("operation", "repository_get")
            return self.database.get_consumer_offset(consumer_group, topic, partition)
