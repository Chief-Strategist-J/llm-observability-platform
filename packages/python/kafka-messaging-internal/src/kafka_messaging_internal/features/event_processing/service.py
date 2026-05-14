"""Event processing service."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
import uuid

from opentelemetry import trace
from kafka_messaging_internal.shared.ports.database_port import DatabasePort, ConsumerOffset
from kafka_messaging_internal.shared.types.events import EventRecord
from kafka_messaging_internal.shared.errors.exceptions import ValidationError, BusinessError


@dataclass
class ProcessingResult:
    """Result of event processing."""
    success: bool
    event_id: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ProcessingResult to dictionary."""
        result = {
            "success": self.success
        }
        if self.event_id:
            result["event_id"] = self.event_id
        if self.error:
            result["error"] = self.error
        if self.metadata:
            result.update(self.metadata)
        return result
    
    def __iter__(self):
        """Make ProcessingResult iterable for FastAPI serialization."""
        return iter(self.to_dict().items())


class EventProcessingService:
    """Service for processing events with business logic."""
    
    def __init__(self, database: DatabasePort):
        """Initialize event processing service with database port."""
        self.database = database
        self.tracer = trace.get_tracer(__name__)
    
    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single event."""
        with self.tracer.start_as_current_span("event_processing.process_event") as span:
            span.set_attributes({
                "service.name": "kafka-messaging-internal",
                "feature.name": "event_processing",
                "api.version": "v1",
                "event.topic": event.get('topic', 'unknown'),
                "event.has_key": str(bool(event.get('key')))
            })
            
            try:
                # Validate event
                if not event.get('topic'):
                    return {
                        "success": False,
                        "event_id": None,
                        "result": None,
                        "error": "Event topic cannot be empty",
                        "metadata": {"error_type": "validation"}
                    }
                if not event.get('value'):
                    return {
                        "success": False,
                        "event_id": None,
                        "result": None,
                        "error": "Event value cannot be empty",
                        "metadata": {"error_type": "validation"}
                    }
                
                span.set_attribute("validation.status", "passed")
                
                # Construct EventRecord
                event_record = EventRecord(
                    event_id=event.get('event_id', str(uuid.uuid4())),
                    topic=event.get('topic'),
                    partition=event.get('partition', 0),
                    offset=event.get('offset', 0),
                    key=event.get('key'),
                    value=event.get('value'),
                    timestamp=event.get('timestamp', datetime.now(timezone.utc)),
                    headers=event.get('headers')
                )
                
                # Save event to database
                with self.tracer.start_as_current_span("database.save_event") as db_span:
                    db_span.set_attributes({
                        "operation.name": "save_event",
                        "database.operation": "insert"
                    })
                    db_event_id = await self.database.save_event(event_record)
                    db_span.set_attribute("event.id", db_event_id)
                
                # Mark event as processed
                with self.tracer.start_as_current_span("mark_event_processed") as mark_span:
                    mark_span.set_attributes({
                        "operation.name": "mark_event_processed",
                        "database.operation": "update"
                    })
                    await self.mark_event_processed(db_event_id, None)
                
                return {
                    "success": True,
                    "event_id": db_event_id,
                    "result": {"processed": True},
                    "error": None,
                    "metadata": {"processed_at": datetime.now(timezone.utc).isoformat()}
                }
                
            except ValidationError as e:
                span.set_attributes({
                    "processing.status": "validation_error",
                    "error.message": str(e),
                    "error.type": "ValidationError"
                })
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                return {
                    "success": False,
                    "event_id": None,
                    "result": None,
                    "error": str(e),
                    "metadata": {"error_type": "validation"}
                }
                
            except Exception as e:
                span.record_error(e)
                span.set_attributes({
                    "processing.status": "system_error",
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
    
    async def process_events_batch(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple events in batch."""
        with self.tracer.start_as_current_span("event_processing.process_events_batch") as span:
            span.set_attributes({
                "service.name": "kafka-messaging-internal",
                "feature.name": "event_processing",
                "batch.size": str(len(events)),
                "api.version": "v1"
            })
            
            results = []
            successful_count = 0
            error_count = 0
            
            try:
                valid_records = []
                results = [None] * len(events)
                
                # Validation phase
                for i, event in enumerate(events):
                    with self.tracer.start_as_current_span(f"process_event_{i}") as event_span:
                        event_span.set_attributes({
                            "event.index": str(i),
                            "event.topic": event.get('topic', 'unknown')
                        })
                        
                        try:
                            if not event.get('topic'):
                                raise ValidationError("Event topic cannot be empty")
                            if not event.get('value'):
                                raise ValidationError("Event value cannot be empty")
                            
                            event_span.set_attribute("validation.status", "passed")
                            
                            record = EventRecord(
                                event_id=event.get('event_id', str(uuid.uuid4())),
                                topic=event.get('topic'),
                                partition=event.get('partition', 0),
                                offset=event.get('offset', 0),
                                key=event.get('key'),
                                value=event.get('value'),
                                timestamp=event.get('timestamp', datetime.now(timezone.utc)),
                                headers=event.get('headers')
                            )
                            valid_records.append((i, record, event_span))
                            
                        except ValidationError as ve:
                            results[i] = {
                                "success": False,
                                "error": str(ve),
                                "metadata": {"error_type": "validation"}
                            }
                            error_count += 1
                            event_span.set_attribute("processing.error", str(ve))
                            event_span.record_exception(ve)
                            event_span.set_status(trace.Status(trace.StatusCode.ERROR, str(ve)))
                
                # Batch save phase
                if valid_records:
                    records_to_save = [r[1] for r in valid_records]
                    try:
                        with self.tracer.start_as_current_span("database.save_events_batch") as db_span:
                            db_span.set_attributes({
                                "operation.name": "save_events_batch",
                                "database.operation": "insert",
                                "batch.size": str(len(records_to_save))
                            })
                            event_ids = await self.database.save_events_batch(records_to_save)
                            
                        for i, record, event_span in valid_records:
                            results[i] = {
                                "success": True,
                                "event_id": record.event_id
                            }
                            successful_count += 1
                            event_span.set_attribute("event.id", record.event_id)
                            event_span.set_attribute("processing.status", "success")
                    except Exception as e:
                        error_msg = str(e)
                        for i, record, event_span in valid_records:
                            results[i] = {
                                "success": False,
                                "error": error_msg,
                                "metadata": {"error_type": "system"}
                            }
                            error_count += 1
                            event_span.set_attribute("processing.error", error_msg)
                            event_span.record_exception(e)
                            event_span.set_status(trace.Status(trace.StatusCode.ERROR, error_msg))
                
                span.set_attributes({
                    "batch.successful_count": str(successful_count),
                    "batch.error_count": str(error_count),
                    "processing.status": "completed"
                })
                span.set_status(trace.Status(trace.StatusCode.OK))
                
                return results
                
            except Exception as e:
                span.record_error(e)
                span.set_attributes({
                    "processing.status": "batch_error",
                    "error.type": "Exception"
                })
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            
            return results
    
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
                with self.tracer.start_as_current_span("database.get_event") as db_span:
                    db_span.set_attributes({
                        "operation.name": "get_event",
                        "database.operation": "select",
                        "event.id": event_id
                    })
                    event = await self.database.get_event(event_id)
                    
                    if event:
                        result = {
                            "event_id": event.event_id,
                            "topic": event.topic,
                            "value": event.value,
                            "timestamp": event.timestamp.isoformat() if event.timestamp else None
                        }
                        span.set_attributes({
                            "event.found": "true",
                            "event.topic": event.topic
                        })
                        db_span.set_attribute("event.found", "true")
                        return result
                    else:
                        span.set_attribute("event.found", "false")
                        db_span.set_attribute("event.found", "false")
                        return None
                        
            except Exception as e:
                span.record_error(e)
                span.set_attributes({
                    "processing.status": "error",
                    "error.type": "Exception"
                })
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise BusinessError(f"Failed to get event: {str(e)}")
    
    async def query_events(self, filters: Dict[str, Any]) -> List[EventRecord]:
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
                topic = filters.get('topic')
                limit = filters.get('limit', 100)
                offset = filters.get('offset', 0)
                
                # Edge case validation
                if limit <= 0:
                    raise ValidationError("Limit must be greater than 0")
                if offset < 0:
                    raise ValidationError("Offset cannot be negative")
                if limit > 1000:  # Prevent excessive queries
                    raise ValidationError("Limit cannot exceed 1000")
                
                with self.tracer.start_as_current_span("database.get_events_by_topic") as db_span:
                    db_span.set_attributes({
                        "operation.name": "get_events_by_topic",
                        "database.operation": "select",
                        "query.topic": topic or "all",
                        "query.limit": str(limit),
                        "query.offset": str(offset)
                    })
                    events = await self.database.get_events_by_topic(topic, limit, offset)
                    
                    span.set_attributes({
                        "query.result_count": str(len(events)),
                        "processing.status": "success"
                    })
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    
                    return events
                    
            except ValidationError as e:
                span.set_attributes({
                    "processing.status": "validation_error",
                    "error.message": str(e),
                    "error.type": "ValidationError"
                })
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
                
            except Exception as e:
                span.record_error(e)
                span.set_attributes({
                    "processing.status": "error",
                    "error.type": "Exception"
                })
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                # Don't wrap in BusinessError for validation issues - let ValidationError propagate
                if "validation" in str(e).lower() or "limit" in str(e).lower() or "offset" in str(e).lower():
                    raise ValidationError(str(e))
                raise BusinessError(f"Failed to query events: {str(e)}")
    
    async def update_consumer_offset(self, offset_data: Dict[str, Any]) -> ProcessingResult:
        """Update consumer offset."""
        with self.tracer.start_as_current_span("event_processing.update_consumer_offset") as span:
            span.set_attributes({
                "service.name": "kafka-messaging-internal",
                "feature.name": "event_processing",
                "api.version": "v1",
                "consumer.group": offset_data.get('consumer_group', 'unknown'),
                "consumer.topic": offset_data.get('topic', 'unknown'),
                "consumer.partition": str(offset_data.get('partition', 0))
            })
            
            try:
                # Edge case validation
                if not offset_data.get('consumer_group'):
                    raise ValidationError("Consumer group cannot be empty")
                if not offset_data.get('topic'):
                    raise ValidationError("Topic cannot be empty")
                if offset_data.get('partition', 0) < 0:
                    raise ValidationError("Partition cannot be negative")
                if offset_data.get('offset', 0) < 0:
                    raise ValidationError("Offset cannot be negative")
                
                from kafka_messaging_internal.shared.ports.database_port import ConsumerOffset
                
                consumer_offset = ConsumerOffset(
                    consumer_group=offset_data.get('consumer_group'),
                    topic=offset_data.get('topic'),
                    partition=offset_data.get('partition', 0),
                    offset=offset_data.get('offset', 0)
                )
                
                with self.tracer.start_as_current_span("database.save_consumer_offset") as db_span:
                    db_span.set_attributes({
                        "operation.name": "save_consumer_offset",
                        "database.operation": "upsert",
                        "consumer.group": consumer_offset.consumer_group,
                        "consumer.topic": consumer_offset.topic
                    })
                    success = await self.database.save_consumer_offset(consumer_offset)
                    db_span.set_attribute("operation.success", str(success))
                
                result = ProcessingResult(
                    success=success,
                    event_id=None,
                    error=None,
                    metadata={
                        "consumer_group": consumer_offset.consumer_group,
                        "topic": consumer_offset.topic,
                        "partition": consumer_offset.partition,
                        "offset": consumer_offset.offset,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                )
                
                span.set_attributes({
                    "processing.status": "success" if success else "failed",
                    "operation.success": str(success)
                })
                span.set_status(trace.Status(trace.StatusCode.OK))
                
                return result
                
            except ValidationError as e:
                span.set_attributes({
                    "processing.status": "validation_error",
                    "error.message": str(e),
                    "error.type": "ValidationError"
                })
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                return ProcessingResult(
                    success=False,
                    event_id=None,
                    error=str(e),
                    metadata={
                        "consumer_group": offset_data.get('consumer_group', ''),
                        "topic": offset_data.get('topic', ''),
                        "partition": offset_data.get('partition', 0),
                        "offset": offset_data.get('offset', 0),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                )
                
            except Exception as e:
                span.record_error(e)
                span.set_attributes({
                    "processing.status": "error",
                    "error.type": "Exception"
                })
                error_msg = str(e)
                # Prevent ProcessingResult object from being used as error message
                if "ProcessingResult(" in error_msg:
                    error_msg = f"Unexpected error in update_consumer_offset: {type(e).__name__}"
                span.set_status(trace.Status(trace.StatusCode.ERROR, error_msg))
                return ProcessingResult(
                    success=False,
                    event_id=None,
                    error=error_msg,
                    metadata={
                        "consumer_group": offset_data.get('consumer_group', ''),
                        "topic": offset_data.get('topic', ''),
                        "partition": offset_data.get('partition', 0),
                        "offset": offset_data.get('offset', 0),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                )
    
    async def get_consumer_offsets(self, filters: Dict[str, Any]) -> List[ConsumerOffset]:
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
                consumer_group = filters.get('consumer_group')
                topic = filters.get('topic')
                
                # Edge case validation
                if consumer_group and not consumer_group.strip():
                    raise ValidationError("Consumer group cannot be empty string")
                if topic and not topic.strip():
                    raise ValidationError("Topic cannot be empty string")
                
                if consumer_group and topic:
                    with self.tracer.start_as_current_span("database.get_consumer_offset") as db_span:
                        db_span.set_attributes({
                            "operation.name": "get_consumer_offset",
                            "database.operation": "select",
                            "consumer.group": consumer_group,
                            "consumer.topic": topic
                        })
                        offset = await self.database.get_consumer_offset(consumer_group, topic, 0)
                        result = [offset] if offset else []
                        
                        span.set_attributes({
                            "query.result_count": str(len(result)),
                            "processing.status": "success"
                        })
                        db_span.set_attribute("query.result_count", str(len(result)))
                        return result
                
                # Return empty list if filters are incomplete
                span.set_attributes({
                    "query.result_count": "0",
                    "processing.status": "success",
                    "filter.incomplete": "true"
                })
                return []
                
            except ValidationError as e:
                span.set_attributes({
                    "processing.status": "validation_error",
                    "error.message": str(e),
                    "error.type": "ValidationError"
                })
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
                
            except Exception as e:
                span.record_error(e)
                span.set_attributes({
                    "processing.status": "error",
                    "error.type": "Exception"
                })
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise BusinessError(f"Failed to get consumer offsets: {str(e)}")
    
    async def mark_event_processed(self, event_id: str, error: Optional[str] = None) -> bool:
        """Mark an event as processed."""
        with self.tracer.start_as_current_span("event_processing.mark_event_processed") as span:
            span.set_attributes({
                "service.name": "kafka-messaging-internal",
                "feature.name": "event_processing",
                "api.version": "v1",
                "event.id": event_id,
                "event.has_error": str(bool(error))
            })
            
            try:
                # Edge case validation
                if not event_id or not event_id.strip():
                    raise ValidationError("Event ID cannot be empty")
                
                with self.tracer.start_as_current_span("database.mark_event_processed") as db_span:
                    db_span.set_attributes({
                        "operation.name": "mark_event_processed",
                        "database.operation": "update",
                        "event.id": event_id,
                        "event.has_error": str(bool(error))
                    })
                    result = await self.database.mark_event_processed(event_id, error)
                    db_span.set_attribute("operation.success", str(result))
                
                span.set_attributes({
                    "processing.status": "success",
                    "operation.success": str(result)
                })
                span.set_status(trace.Status(trace.StatusCode.OK))
                
                return result
                
            except ValidationError as e:
                span.set_attributes({
                    "processing.status": "validation_error",
                    "error.message": str(e),
                    "error.type": "ValidationError"
                })
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
                
            except Exception as e:
                span.record_error(e)
                span.set_attributes({
                    "processing.status": "error",
                    "error.type": "Exception"
                })
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise BusinessError(f"Failed to mark event as processed: {str(e)}")
    
    async def get_processing_stats(self, topic: Optional[str] = None) -> Dict[str, Any]:
        """Get processing statistics."""
        with self.tracer.start_as_current_span("event_processing.get_processing_stats") as span:
            span.set_attributes({
                "service.name": "kafka-messaging-internal",
                "feature.name": "event_processing",
                "api.version": "v1",
                "stats.topic": topic or "all"
            })
            
            try:
                # Edge case validation
                if topic and not topic.strip():
                    raise ValidationError("Topic cannot be empty string")
                
                # This would typically query a processing stats table
                # For now, return mock data with proper structure
                stats = {
                    "total_events_processed": 1000,
                    "successful_events": 950,
                    "failed_events": 50,
                    "topic": topic,
                    "last_processed": datetime.now(timezone.utc).isoformat(),
                    "success_rate": 95.0
                }
                
                span.set_attributes({
                    "stats.total_processed": str(stats["total_events_processed"]),
                    "stats.successful": str(stats["successful_events"]),
                    "stats.failed": str(stats["failed_events"]),
                    "stats.success_rate": str(stats["success_rate"]),
                    "processing.status": "success"
                })
                span.set_status(trace.Status(trace.StatusCode.OK))
                
                return stats
                
            except ValidationError as e:
                span.set_attributes({
                    "processing.status": "validation_error",
                    "error.message": str(e),
                    "error.type": "ValidationError"
                })
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
                
            except Exception as e:
                span.record_error(e)
                span.set_attributes({
                    "processing.status": "error",
                    "error.type": "Exception"
                })
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise BusinessError(f"Failed to get processing stats: {str(e)}")


class ValidationError(Exception):
    """Validation error for event processing."""
    pass


class BusinessError(Exception):
    """Business logic error for event processing."""
    pass
