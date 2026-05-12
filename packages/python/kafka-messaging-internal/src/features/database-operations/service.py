"""Database operations business logic service."""

from typing import Any, Dict, List, Optional

from opentelemetry import trace
from ...shared.errors.codes import validation_failed, business_error
from ...shared.utils.validation import validate_pagination_params
from ...shared.ports.database_port import DatabasePort


class DatabaseOperationsService:
    """Business logic for database operations with SRP compliance."""
    
    def __init__(self, database: DatabasePort):
        self.database = database
        self.tracer = trace.get_tracer(__name__)
    
    def get_event_count(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get event count with optional topic filter."""
        with self.tracer.start_as_current_span("database_operations.get_event_count") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "get_event_count")
            
            try:
                topic = filters.get('topic')
                
                if topic:
                    # Validate topic
                    if not isinstance(topic, str) or not topic.strip():
                        span.record_error("Topic must be a non-empty string")
                        raise validation_failed("Topic must be a non-empty string")
                
                # Get count
                count = self.database.get_event_count(topic)
                
                return {
                    "count": count,
                    "topic": topic or "all"
                }
                
            except Exception as e:
                span.record_error(e)
                raise business_error(f"Processing failed: {str(e)}")
    
    def delete_events_by_topic(self, topic: str) -> Dict[str, Any]:
        """Delete events by topic with business validation."""
        with self.tracer.start_as_current_span("database_operations.delete_events_by_topic") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "delete_events_by_topic")
            span.set_attribute("topic", topic)
            
            try:
                # Validate topic
                if not isinstance(topic, str) or not topic.strip():
                    span.record_error("Topic must be a non-empty string")
                    raise validation_failed("Topic must be a non-empty string")
                
                # Business rule: Don't allow deletion of critical topics
                critical_topics = ['system-events', 'audit-events', 'security-events']
                if topic.lower() in [t.lower() for t in critical_topics]:
                    span.record_error(f"Cannot delete events from critical topic: {topic}")
                    raise business_error(f"Cannot delete events from critical topic: {topic}")
                
                # Delete events
                deleted_count = self.database.delete_events_by_topic(topic)
                
                span.set_attribute("deleted_count", str(deleted_count))
                span.set_attribute("success", "true")
                
                return {
                    "topic": topic,
                    "deleted_count": deleted_count,
                    "success": True
                }
                
            except Exception as e:
                span.record_error(e)
                raise business_error(f"Processing failed: {str(e)}")
    
    def get_unprocessed_events(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get unprocessed events with pagination."""
        with self.tracer.start_as_current_span("database_operations.get_unprocessed_events") as span:
            span.set_attribute("feature.name", "database-operations")
            span.set_attribute("operation", "get_unprocessed_events")
            
            try:
                # Validate pagination parameters
                is_valid, error, cleaned_params = validate_pagination_params(filters)
                if not is_valid:
                    span.record_error("Validation failed")
                    raise validation_failed("Validation failed")
                        code="VALIDATION_INVALID_REQUEST",
                        message=error or "Invalid pagination parameters"
                    )
                    raise validation_error
                
                limit = cleaned_params['limit']
                
                # Get unprocessed events
                events = self.database.get_unprocessed_events(limit)
                
                # Convert to response format
                event_list = []
                for event in events:
                    event_list.append({
                        "event_id": event.event_id,
                        "topic": event.topic,
                        "partition": event.partition,
                        "offset": event.offset,
                        "key": event.key,
                        "value": event.value,
                        "timestamp": event.timestamp.isoformat(),
                        "headers": event.headers,
                        "processed": event.processed,
                        "error": event.error,
                        "created_at": event.created_at.isoformat() if event.created_at else None
                    })
                
                span.set_attribute("event_count", str(len(event_list)))
                span.set_attribute("success", "true")
                
                return {
                    "events": event_list,
                    "count": len(event_list),
                    "limit": limit
                }
                
                raise
            except Exception as e:
                span.record_error(e)
                raise business_error(f"Processing failed: {str(e)}")
