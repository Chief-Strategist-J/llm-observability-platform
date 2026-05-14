"""Public interface for event processing feature."""

from typing import Any, Dict, List, Optional
from opentelemetry import trace
from .service import EventProcessingService
from kafka_messaging_internal.shared.di.container import get_container
from kafka_messaging_internal.shared.ports.database_port import DatabasePort
from kafka_messaging_internal.shared.errors.exceptions import ValidationError


class EventProcessing:
    """Event processing feature entry point following SRP rules."""
    
    def __init__(self):
        self.tracer = trace.get_tracer(__name__)
        self.container = get_container()
        
        with self.tracer.start_as_current_span("event_processing_initialization") as span:
            span.set_attributes({
                "service.name": "kafka-messaging-internal",
                "feature.name": "event_processing",
                "api.version": "v1"
            })
            
            try:
                self.database = self.container.get(DatabasePort)
                self.service = EventProcessingService(self.database)
                
                span.set_status(trace.Status(trace.StatusCode.OK))
                
            except Exception as e:
                span.record_error(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
    
    async def process_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single event."""
        with self.tracer.start_as_current_span("event_processing.process_event") as span:
            span.set_attributes({
                "service.name": "kafka-messaging-internal",
                "feature.name": "event_processing",
                "api.version": "v1",
                "event.topic": event_data.get('topic', 'unknown')
            })
            
            try:
                # Edge case validation
                if not event_data:
                    raise ValidationError("Event data cannot be empty")
                
                result = await self.service.process_event(event_data)
                
                span.set_attributes({
                    "processing.status": "success" if result.get("success") else "failed",
                    "event.id": result.get("event_id") or "none"
                })
                span.set_status(trace.Status(trace.StatusCode.OK))
                
                return result
                
            except ValidationError:
                raise
            except Exception as e:
                span.record_error(e)
                span.set_attributes({
                    "processing.status": "error",
                    "error.type": "Exception"
                })
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                
                return {
                    "success": False,
                    "event_id": None,
                    "result": None,
                    "error": str(e),
                    "metadata": {"error_type": "system"}
                }
    
    async def process_events_batch(self, events_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process multiple events in batch."""
        with self.tracer.start_as_current_span("event_processing.process_events_batch") as span:
            span.set_attributes({
                "service.name": "kafka-messaging-internal",
                "feature.name": "event_processing",
                "api.version": "v1",
                "batch.size": str(len(events_data))
            })
            
            try:
                # Edge case validation
                if not events_data:
                    raise ValidationError("Events data cannot be empty")
                if len(events_data) > 1000:  # Prevent excessive batches
                    raise ValidationError("Batch size cannot exceed 1000")
                
                result_list = await self.service.process_events_batch(events_data)
                
                # Transform list result to expected format
                successful_count = 0
                failed_count = 0
                event_ids = []
                
                if isinstance(result_list, list):
                    for item in result_list:
                        if isinstance(item, dict):
                            if item.get("success"):
                                successful_count += 1
                                if item.get("event_id"):
                                    event_ids.append(item["event_id"])
                            else:
                                failed_count += 1
                
                result = {
                    "event_ids": event_ids,
                    "count": len(event_ids),
                    "success": failed_count == 0
                }
                
                span.set_attributes({
                    "batch.successful_count": str(successful_count),
                    "batch.failed_count": str(failed_count),
                    "processing.status": "success"
                })
                span.set_status(trace.Status(trace.StatusCode.OK))
                
                return result
                
            except ValidationError:
                raise
            except Exception as e:
                span.record_error(e)
                span.set_attributes({
                    "processing.status": "error",
                    "error.type": "Exception"
                })
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                
                return {
                    "results": [],
                    "total_processed": 0,
                    "successful_count": 0,
                    "failed_count": 0,
                    "error": str(e)
                }
    
    async def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get event by ID."""
        with self.tracer.start_as_current_span("event_processing.get_event") as span:
            span.set_attributes({
                "service.name": "kafka-messaging-internal",
                "feature.name": "event_processing",
                "api.version": "v1",
                "event.id": event_id
            })
            
            try:
                # Edge case validation
                if not event_id or not event_id.strip():
                    raise ValidationError("Event ID cannot be empty")
                
                event = await self.service.get_event(event_id)
                
                span.set_attributes({
                    "event.found": "true" if event else "false",
                    "processing.status": "success"
                })
                span.set_status(trace.Status(trace.StatusCode.OK))
                
                return event
                
            except Exception as e:
                span.record_error(e)
                span.set_attributes({
                    "processing.status": "error",
                    "error.type": "Exception"
                })
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                return None
    
    async def query_events(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Query events with filters."""
        with self.tracer.start_as_current_span("event_processing.query_events") as span:
            span.set_attributes({
                "service.name": "kafka-messaging-internal",
                "feature.name": "event_processing",
                "api.version": "v1",
                "query.topic": filters.get('topic', 'all'),
                "query.limit": str(filters.get('limit', 100)),
                "query.offset": str(filters.get('offset', 0))
            })
            
            try:
                # Edge case validation
                if not filters:
                    raise ValidationError("Filters cannot be empty")
                
                events = await self.service.query_events(filters)
                
                response = {
                    "events": [{"event_id": e.event_id, "topic": e.topic, "value": e.value, "timestamp": e.timestamp.isoformat() if e.timestamp else None} for e in events],
                    "count": len(events),
                    "filters": filters
                }
                
                span.set_attributes({
                    "query.result_count": str(len(events)),
                    "processing.status": "success"
                })
                span.set_status(trace.Status(trace.StatusCode.OK))
                
                return response
                
            except Exception as e:
                span.record_error(e)
                span.set_attributes({
                    "processing.status": "error",
                    "error.type": "Exception"
                })
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                
                return {
                    "events": [],
                    "count": 0,
                    "filters": filters,
                    "error": str(e)
                }
    
    async def update_consumer_offset(self, offset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update consumer offset."""
        with self.tracer.start_as_current_span("event_processing.update_consumer_offset") as span:
            span.set_attributes({
                "service.name": "kafka-messaging-internal",
                "feature.name": "event_processing",
                "api.version": "v1",
                "consumer.group": offset_data.get('consumer_group', 'unknown'),
                "consumer.topic": offset_data.get('topic', 'unknown')
            })
            
            try:
                # Edge case validation
                if not offset_data:
                    raise ValidationError("Offset data cannot be empty")
                
                result = await self.service.update_consumer_offset(offset_data)
                
                span.set_attributes({
                    "processing.status": "success" if result.get("success") else "failed",
                    "operation.success": str(result.get("success"))
                })
                span.set_status(trace.Status(trace.StatusCode.OK))
                
                return result
                
            except ValidationError:
                raise
            except Exception as e:
                span.record_error(e)
                span.set_attributes({
                    "processing.status": "error",
                    "error.type": "Exception"
                })
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                
                return {
                    "success": False,
                    "metadata": {"error_type": "system", "error": str(e)}
                }
    
    async def get_consumer_offsets(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get consumer offsets."""
        with self.tracer.start_as_current_span("event_processing.get_consumer_offsets") as span:
            span.set_attributes({
                "service.name": "kafka-messaging-internal",
                "feature.name": "event_processing",
                "api.version": "v1",
                "filter.consumer_group": filters.get('consumer_group', 'all'),
                "filter.topic": filters.get('topic', 'all')
            })
            
            try:
                # Edge case validation
                if not filters:
                    raise ValidationError("Filters cannot be empty")
                
                offsets = await self.service.get_consumer_offsets(filters)
                
                response = {
                    "offsets": [{"consumer_group": o.consumer_group, "topic": o.topic, "partition": o.partition, "offset": o.offset, "updated_at": o.updated_at.isoformat() if o.updated_at else None} for o in offsets],
                    "count": len(offsets)
                }
                
                span.set_attributes({
                    "query.result_count": str(len(offsets)),
                    "processing.status": "success"
                })
                span.set_status(trace.Status(trace.StatusCode.OK))
                
                return response
                
            except Exception as e:
                span.record_error(e)
                span.set_attributes({
                    "processing.status": "error",
                    "error.type": "Exception"
                })
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                
                return {
                    "offsets": [],
                    "count": 0,
                    "error": str(e)
                }


# Factory function for DI container
def create_event_processing() -> EventProcessing:
    """Create event processing feature instance."""
    return EventProcessing()
