from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from fastapi import HTTPException, status, APIRouter
from pydantic import BaseModel, Field

from domain.ports.database_port import EventRecord, ConsumerOffset, DatabasePort
from domain.ports.event_writer_port import EventWriterPort
from domain.ports.event_reader_port import EventReaderPort
from domain.ports.event_management_port import EventManagementPort
from domain.ports.offset_port import OffsetPort
from domain.ports.count_port import CountPort
from domain.ports.queue_port import QueuePort
from domain.ports.idempotency_port import IdempotencyPort
from domain.ports.metrics_port import MetricsPort
from domain.ports.persistence_strategy import PersistenceStrategy
from application.api.v1.validators import Preconditions, Postconditions, ValidationError
from application.api.v1.error_handler import (
    raise_validation_error,
    raise_not_found_error,
    raise_conflict_error,
    raise_too_many_requests_error,
    raise_internal_error
)
from application.services.event_validator import EventValidator, EventRequestParams, QueryParams, ConsumerOffsetParams
from application.services.idempotency_service import IdempotencyService
from application.services.queue_service import QueueService


@dataclass
class DatabaseAPIConfig:
    event_writer: EventWriterPort
    event_reader: EventReaderPort
    event_manager: EventManagementPort
    offset_port: OffsetPort
    count_port: CountPort
    queue: QueuePort = None
    idempotency_store: IdempotencyPort = None
    metrics: MetricsPort = None
    persistence_strategy: PersistenceStrategy = None


class EventRecordRequest(BaseModel):
    event_id: Optional[str] = Field(None, description="Unique event identifier for idempotency")
    topic: str = Field(..., description="Kafka topic name")
    partition: int = Field(..., description="Kafka partition number")
    offset: int = Field(..., description="Kafka message offset")
    key: Optional[str] = Field(None, description="Message key")
    value: Any = Field(..., description="Message value (any JSON-serializable type)")
    timestamp: Optional[datetime] = Field(None, description="Event timestamp")
    headers: Optional[Dict[str, Any]] = Field(None, description="Event headers")
    priority: Optional[str] = Field("normal", description="Priority: high, normal, low")


class EventRecordResponse(BaseModel):
    event_id: str
    topic: str
    partition: int
    offset: int
    key: Optional[str]
    value: Any
    timestamp: datetime
    headers: Optional[Dict[str, Any]]
    processed: bool
    error: Optional[str]
    created_at: datetime


class BatchEventRequest(BaseModel):
    events: List[EventRecordRequest] = Field(..., description="List of events to save")


class BatchEventResponse(BaseModel):
    event_ids: List[str]
    count: int
    success: bool


class ConsumerOffsetRequest(BaseModel):
    consumer_group: str = Field(..., description="Consumer group name")
    topic: str = Field(..., description="Kafka topic name")
    partition: int = Field(..., description="Kafka partition number")
    offset: int = Field(..., description="Consumer offset value")


class ConsumerOffsetResponse(BaseModel):
    consumer_group: str
    topic: str
    partition: int
    offset: int
    updated_at: datetime


class EventQueryParams(BaseModel):
    topic: str = Field(..., min_length=1, description="Topic to query")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of events to return")
    offset: int = Field(0, ge=0, description="Number of events to skip")


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class DatabaseAPI:
    def __init__(self, config: DatabaseAPIConfig):
        self._event_writer = config.event_writer
        self._event_reader = config.event_reader
        self._event_manager = config.event_manager
        self._offset_port = config.offset_port
        self._count_port = config.count_port
        self._queue = config.queue
        self._idempotency_store = config.idempotency_store
        self._metrics = config.metrics
        self._persistence_strategy = config.persistence_strategy

        self._validator = EventValidator()
        if config.idempotency_store:
            self._idempotency_service = IdempotencyService(config.idempotency_store)
        if config.queue and config.metrics:
            self._queue_service = QueueService(config.queue, config.metrics)

        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        @self.router.post("/events", response_model=EventRecordResponse)
        async def save_event_route(request: EventRecordRequest):
            return await self.save_event(request)

        @self.router.post("/events/batch", response_model=BatchEventResponse)
        async def save_events_batch_route(request: BatchEventRequest):
            return await self.save_events_batch(request)

        @self.router.get("/events/{event_id}", response_model=EventRecordResponse)
        def get_event_route(event_id: str):
            return self.get_event(event_id)

        @self.router.get("/events", response_model=List[EventRecordResponse])
        def get_events_by_topic_route(topic: str, limit: int = 100, offset: int = 0):
            return self.get_events_by_topic(topic, limit, offset)

        @self.router.post("/events/{event_id}/processed")
        def mark_event_processed_route(event_id: str):
            return self.mark_event_processed(event_id)

        @self.router.post("/consumer-offsets")
        def save_consumer_offset_route(request: ConsumerOffsetRequest):
            return self.save_consumer_offset(request)

        @self.router.get("/consumer-offsets/{consumer_group}/{topic}/{partition}", response_model=ConsumerOffsetResponse)
        def get_consumer_offset_route(consumer_group: str, topic: str, partition: int):
            return self.get_consumer_offset(consumer_group, topic, partition)

        @self.router.delete("/events/{topic}")
        def delete_events_by_topic_route(topic: str):
            return self.delete_events_by_topic(topic)

        @self.router.get("/events/{topic}/count")
        def get_event_count_route(topic: str):
            return self.get_event_count(topic)

    async def save_event(self, request: EventRecordRequest) -> EventRecordResponse:
        params = EventRequestParams(request.topic, request.partition, request.offset)
        self._validator.validate_event_request(params)

        if self._idempotency_service:
            await self._idempotency_service.check_and_handle_duplicate(request.event_id)

        event = self._build_event_record(request)

        if self._persistence_strategy:
            event_id = await self._persistence_strategy.save(event)
        elif self._queue_service:
            shard_key = self._get_shard_key(event.key)
            await self._queue_service.enqueue_event(event, shard_key, request.priority)
            event_id = request.event_id or f"queued-{shard_key[0]}-{shard_key[1]}"
        else:
            try:
                event_id = self._event_writer.save_event(event)
                Preconditions.validate_not_none(event_id, "save_event")
            except ValidationError as e:
                raise_internal_error(str(e))
            except Exception as e:
                raise_internal_error(f"Failed to save event: {str(e)}")

        return self._build_event_response(event_id, event)

    async def save_events_batch(self, request: BatchEventRequest) -> BatchEventResponse:
        self._validator.validate_batch_request(request.events)

        events = [self._build_event_record(e) for e in request.events]

        try:
            event_ids = self._event_writer.save_events_batch(events)
            Preconditions.validate_not_none(event_ids, "save_events_batch")
            Preconditions.validate_not_empty_list(event_ids, "save_events_batch")
            return BatchEventResponse(
                event_ids=event_ids,
                count=len(event_ids),
                success=True
            )
        except ValidationError as e:
            raise_internal_error(str(e))
        except Exception as e:
            raise_internal_error(f"Failed to save events batch: {str(e)}")

    def get_event(self, event_id: str) -> EventRecordResponse:
        self._validator.validate_event_id(event_id)

        try:
            event = self._event_reader.get_event(event_id)
            if not event:
                raise_not_found_error(f"Event with id {event_id} not found. Verify the event ID is correct.")
            return self._build_event_response(event_id, event)
        except HTTPException:
            raise
        except Exception as e:
            raise_internal_error(f"Failed to get event: {str(e)}")

    def get_events_by_topic(self, topic: str, limit: int = 100, offset: int = 0) -> List[EventRecordResponse]:
        params = QueryParams(topic, limit, offset)
        self._validator.validate_query_params(params)

        try:
            events = self._event_reader.get_events_by_topic(topic, limit=limit, offset=offset)
            return [self._build_event_response(str(i), e) for i, e in enumerate(events)]
        except Exception as e:
            raise_internal_error(f"Failed to get events by topic: {str(e)}")

    def get_unprocessed_events(self, limit: int = 100) -> List[EventRecordResponse]:
        self._validator.validate_limit(limit)

        try:
            events = self._event_reader.get_unprocessed_events(limit=limit)
            return [self._build_event_response(str(i), e) for i, e in enumerate(events)]
        except Exception as e:
            raise_internal_error(f"Failed to get unprocessed events: {str(e)}")

    def mark_event_processed(self, event_id: str) -> Dict[str, bool]:
        self._validator.validate_event_id(event_id)

        try:
            success = self._event_manager.mark_event_processed(event_id)
            Postconditions.validate_success(success, "mark_event_processed")
            return {"success": True}
        except ValidationError as e:
            raise_not_found_error(str(e))
        except Exception as e:
            raise_internal_error(f"Failed to mark event as processed: {str(e)}")

    def save_consumer_offset(self, request: ConsumerOffsetRequest) -> Dict[str, bool]:
        params = ConsumerOffsetParams(request.consumer_group, request.topic, request.partition, request.offset)
        self._validator.validate_consumer_offset(params)

        offset = ConsumerOffset(
            consumer_group=request.consumer_group,
            topic=request.topic,
            partition=request.partition,
            offset=request.offset
        )

        try:
            success = self._offset_port.save_consumer_offset(offset)
            Postconditions.validate_success(success, "save_consumer_offset")
            return {"success": True}
        except ValidationError as e:
            raise_internal_error(str(e))
        except Exception as e:
            raise_internal_error(f"Failed to save consumer offset: {str(e)}")

    def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> ConsumerOffsetResponse:
        params = ConsumerOffsetParams(consumer_group, topic, partition, 0)
        self._validator.validate_consumer_offset(params)

        try:
            offset = self._offset_port.get_consumer_offset(consumer_group, topic, partition)
            if not offset:
                raise_not_found_error(f"Consumer offset not found for group '{consumer_group}', topic '{topic}', partition {partition}. Verify the offset exists.")
            return ConsumerOffsetResponse(
                consumer_group=offset.consumer_group,
                topic=offset.topic,
                partition=offset.partition,
                offset=offset.offset,
                updated_at=offset.updated_at
            )
        except HTTPException:
            raise
        except Exception as e:
            raise_internal_error(f"Failed to get consumer offset: {str(e)}")

    def delete_events_by_topic(self, topic: str) -> Dict[str, int]:
        self._validator.validate_event_id(topic)

        try:
            count = self._event_manager.delete_events_by_topic(topic)
            return {"deleted_count": count}
        except Exception as e:
            raise_internal_error(f"Failed to delete events: {str(e)}")

    def get_event_count(self, topic: Optional[str] = None) -> Dict[str, int]:
        try:
            count = self._count_port.get_event_count(topic)
            return {"count": count}
        except Exception as e:
            raise_internal_error(f"Failed to get event count: {str(e)}")

    def _build_event_record(self, request) -> EventRecord:
        return EventRecord(
            topic=request.topic,
            partition=request.partition,
            offset=request.offset,
            key=request.key,
            value=request.value,
            timestamp=request.timestamp or datetime.utcnow(),
            headers=request.headers
        )

    def _get_shard_key(self, key: Optional[str]) -> Tuple[int, int]:
        get_shard_method = getattr(self._event_writer, '_get_shard', None)
        if get_shard_method:
            return get_shard_method(key)
        return (0, 0)

    def _build_event_response(self, event_id: str, event: EventRecord) -> EventRecordResponse:
        return EventRecordResponse(
            event_id=event_id,
            topic=event.topic,
            partition=event.partition,
            offset=event.offset,
            key=event.key,
            value=event.value,
            timestamp=event.timestamp,
            headers=event.headers,
            processed=event.processed,
            error=event.error,
            created_at=event.created_at
        )
