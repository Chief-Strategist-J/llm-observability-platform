"""Event processing business logic service."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from opentelemetry import trace
from ...shared.errors.codes import validation_failed, business_error
from ...shared.utils.validation import validate_event_record, validate_pagination_params, validate_batch_request
from ...shared.utils.datetime_utils import utc_now, calculate_duration
from ...shared.ports.database_port import DatabasePort, EventRecord, ConsumerOffset


class EventProcessingService:
    """Business logic for event processing with SRP compliance."""
    
    def __init__(self, database: DatabasePort):
        self.database = database
        self.tracer = trace.get_tracer(__name__)
    
    def process_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single event with validation and business rules."""
        with self.tracer.start_as_current_span("event_processing.process_event") as span:
            span.set_attribute("feature.name", "event-processing")
            span.set_attribute("operation", "process_event")
            
            try:
                # Validate input
                is_valid, error = validate_event_record(event_data)
                if not is_valid:
                    raise validation_failed(error or "Invalid event data")
                
                # Create event record
                event = EventRecord(
                    topic=event_data['topic'],
                    partition=event_data['partition'],
                    offset=event_data['offset'],
                    key=event_data.get('key'),
                    value=event_data['value'],
                    timestamp=datetime.fromisoformat(event_data['timestamp'].replace('Z', '+00:00')),
                    headers=event_data.get('headers'),
                    event_id=event_data.get('event_id')
                )
                
                # Check for duplicate processing
                if event.event_id:
                    existing_event = self.database.get_event(event.event_id)
                    if existing_event and existing_event.processed:
                        error_msg = f"Event {event.event_id} has already been processed"
                        raise business_error(error_msg)
                
                # Save event
                saved_event_id = self.database.save_event(event)
                
                # Mark as processed (no business logic for now)
                self.database.mark_event_processed(saved_event_id)
                
                span.set_attribute("event_id", saved_event_id)
                span.set_attribute("success", "true")
                
                return {
                    "event_id": saved_event_id,
                    "success": True,
                    "result": {"stored": True},
                    "error": None
                }
                
                raise
            except Exception as e:
                error = span.record_error(e)
                raise business_error(f"Processing failed: {str(e)}")
    
    def process_events_batch(self, events_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process multiple events in batch."""
        with self.tracer.start_as_current_span("event_processing.process_events_batch") as span:
            span.set_attribute("feature.name", "event-processing")
            span.set_attribute("operation", "process_events_batch")
            span.set_attribute("batch_size", str(len(events_data)))
            
            try:
                # Validate batch
                is_valid, error = validate_batch_request({"records": events_data})
                if not is_valid:
                    span.record_error("Validation failed")
                    raise validation_failed("Validation failed")
                        code="VALIDATION_INVALID_REQUEST",
                        message=error or "Invalid batch request"
                    )
                    raise validation_error
                
                # Process each event
                events = []
                for event_data in events_data:
                    event = EventRecord(
                        topic=event_data['topic'],
                        partition=event_data['partition'],
                        offset=event_data['offset'],
                        key=event_data.get('key'),
                        value=event_data['value'],
                        timestamp=datetime.fromisoformat(event_data['timestamp'].replace('Z', '+00:00')),
                        headers=event_data.get('headers'),
                        event_id=event_data.get('event_id')
                    )
                    events.append(event)
                
                # Save batch
                saved_event_ids = self.database.save_events_batch(events)
                
                # Mark all as processed
                for event_id in saved_event_ids:
                    self.database.mark_event_processed(event_id)
                
                span.set_attribute("success", "true")
                span.set_attribute("processed_count", str(len(saved_event_ids)))
                
                return {
                    "event_ids": saved_event_ids,
                    "count": len(saved_event_ids),
                    "success": True
                }
                
                raise
            except Exception as e:
                error = span.record_error(e)
                raise business_error(f"Processing failed: {str(e)}")
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get event by ID."""
        with self.tracer.start_as_current_span("event_processing.get_event") as span:
            span.set_attribute("feature.name", "event-processing")
            span.set_attribute("operation", "get_event")
            span.set_attribute("event_id", event_id)
            
            try:
                event = self.database.get_event(event_id)
                if event:
                    return {
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
                    }
                return None
                
            except Exception as e:
                error = span.record_error(e)
                raise business_error(f"Processing failed: {str(e)}")
    
    def query_events(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Query events with filters."""
        with self.tracer.start_as_current_span("event_processing.query_events") as span:
            span.set_attribute("feature.name", "event-processing")
            span.set_attribute("operation", "query_events")
            
            try:
                # Validate pagination parameters
                is_valid, error, cleaned_params = validate_pagination_params(filters)
                if not is_valid:
                    span.record_error("Validation failed")
                    raise validation_failed("Validation failed")
                        code="VALIDATION_INVALID_REQUEST",
                        message=error or "Invalid query parameters"
                    )
                    raise validation_error
                
                topic = filters.get('topic')
                limit = cleaned_params['limit']
                offset = cleaned_params['offset']
                
                # Query events
                events = self.database.get_events_by_topic(topic, limit, offset)
                
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
                
                return {
                    "events": event_list,
                    "count": len(event_list),
                    "has_more": len(event_list) == limit
                }
                
                raise
            except Exception as e:
                error = span.record_error(e)
                raise business_error(f"Processing failed: {str(e)}")
    
    def update_consumer_offset(self, offset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update consumer offset."""
        with self.tracer.start_as_current_span("event_processing.update_consumer_offset") as span:
            span.set_attribute("feature.name", "event-processing")
            span.set_attribute("operation", "update_consumer_offset")
            span.set_attribute("consumer_group", offset_data.get('consumer_group', ''))
            
            try:
                # Validate required fields
                required_fields = ['consumer_group', 'topic', 'partition', 'offset']
                for field in required_fields:
                    if field not in offset_data:
                        span.record_error("Validation failed")
                    raise validation_failed("Validation failed")
                            code="VALIDATION_MISSING_FIELD",
                            message=f"Missing required field: {field}"
                        )
                        raise validation_error
                
                # Create offset object
                offset = ConsumerOffset(
                    consumer_group=offset_data['consumer_group'],
                    topic=offset_data['topic'],
                    partition=offset_data['partition'],
                    offset=offset_data['offset']
                )
                
                # Save offset
                success = self.database.save_consumer_offset(offset)
                
                if success:
                    span.set_attribute("success", "true")
                    return {
                        "consumer_group": offset.consumer_group,
                        "topic": offset.topic,
                        "partition": offset.partition,
                        "offset": offset.offset,
                        "updated_at": offset.updated_at.isoformat() if offset.updated_at else utc_now().isoformat()
                    }
                else:
                    span.record_error(f"Business rule violation")
                    raise business_error(f"Business rule violation")
                        code="BUSINESS_PROCESSING_FAILED",
                        message="Failed to update consumer offset"
                    )
                
                raise
            except Exception as e:
                error = span.record_error(e)
                raise business_error(f"Processing failed: {str(e)}")
    
    def get_consumer_offsets(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get consumer offsets."""
        with self.tracer.start_as_current_span("event_processing.get_consumer_offsets") as span:
            span.set_attribute("feature.name", "event-processing")
            span.set_attribute("operation", "get_consumer_offsets")
            
            try:
                consumer_group = filters.get('consumer_group')
                topic = filters.get('topic')
                
                if not consumer_group:
                    span.record_error("Validation failed")
                    raise validation_failed("Validation failed")
                        code="VALIDATION_MISSING_FIELD",
                        message="Missing required field: consumer_group"
                    )
                    raise validation_error
                
                # For now, return empty list as we don't have a get_all_offsets method
                # In a real implementation, you'd add this method to DatabasePort
                offsets = []
                
                if topic:
                    # Get specific offset
                    offset = self.database.get_consumer_offset(consumer_group, topic, 0)  # Default partition 0
                    if offset:
                        offsets.append({
                            "consumer_group": offset.consumer_group,
                            "topic": offset.topic,
                            "partition": offset.partition,
                            "offset": offset.offset,
                            "updated_at": offset.updated_at.isoformat() if offset.updated_at else None
                        })
                else:
                    # Get all offsets for consumer group
                    # This would require extending DatabasePort interface
                    pass
                
                return {
                    "offsets": offsets
                }
                
                raise
            except Exception as e:
                error = span.record_error(e)
                raise business_error(f"Processing failed: {str(e)}")
