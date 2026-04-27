from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import HTTPException, status, APIRouter
from pydantic import BaseModel, Field

from domain.ports.database_port import EventRecord, ConsumerOffset, DatabasePort
from application.api.v1.validators import Preconditions, Postconditions, ValidationError


class EventRecordRequest(BaseModel):
    topic: str = Field(..., description="Kafka topic name")
    partition: int = Field(..., description="Kafka partition number")
    offset: int = Field(..., description="Kafka message offset")
    key: Optional[str] = Field(None, description="Message key")
    value: Any = Field(..., description="Message value (any JSON-serializable type)")
    timestamp: Optional[datetime] = Field(None, description="Event timestamp")
    headers: Optional[Dict[str, Any]] = Field(None, description="Event headers")


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
    def __init__(self, database_port: DatabasePort):
        self._database = database_port
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        @self.router.post("/events", response_model=EventRecordResponse)
        def save_event_route(request: EventRecordRequest):
            return self.save_event(request)

        @self.router.post("/events/batch", response_model=BatchEventResponse)
        def save_events_batch_route(request: BatchEventRequest):
            return self.save_events_batch(request)

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

    def save_event(self, request: EventRecordRequest) -> EventRecordResponse:
        try:
            Preconditions.validate_non_empty_string(request.topic, "topic")
            Preconditions.validate_non_negative(request.partition, "partition")
            Preconditions.validate_non_negative(request.offset, "offset")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        event = EventRecord(
            topic=request.topic,
            partition=request.partition,
            offset=request.offset,
            key=request.key,
            value=request.value,
            timestamp=request.timestamp or datetime.utcnow(),
            headers=request.headers
        )

        try:
            event_id = self._database.save_event(event)
            Preconditions.validate_not_none(event_id, "save_event")
            return self._build_event_response(event_id, event)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save event: {str(e)}"
            )

    def save_events_batch(self, request: BatchEventRequest) -> BatchEventResponse:
        try:
            Preconditions.validate_list_size(request.events, "events", min_size=1, max_size=1000)
            for event in request.events:
                Preconditions.validate_non_empty_string(event.topic, "topic")
                Preconditions.validate_non_negative(event.partition, "partition")
                Preconditions.validate_non_negative(event.offset, "offset")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        events = [
            EventRecord(
                topic=e.topic,
                partition=e.partition,
                offset=e.offset,
                key=e.key,
                value=e.value,
                timestamp=e.timestamp or datetime.utcnow(),
                headers=e.headers
            )
            for e in request.events
        ]

        try:
            event_ids = self._database.save_events_batch(events)
            Preconditions.validate_not_none(event_ids, "save_events_batch")
            Preconditions.validate_not_empty_list(event_ids, "save_events_batch")
            return BatchEventResponse(
                event_ids=event_ids,
                count=len(event_ids),
                success=True
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save events batch: {str(e)}"
            )

    def get_event(self, event_id: str) -> EventRecordResponse:
        try:
            Preconditions.validate_non_empty_string(event_id, "event_id")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            event = self._database.get_event(event_id)
            if not event:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Event with id {event_id} not found. Verify the event ID is correct."
                )
            return self._build_event_response(event_id, event)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get event: {str(e)}"
            )

    def get_events_by_topic(self, topic: str, limit: int = 100, offset: int = 0) -> List[EventRecordResponse]:
        try:
            Preconditions.validate_non_empty_string(topic, "topic")
            Preconditions.validate_range(limit, "limit", min_val=1, max_val=1000)
            Preconditions.validate_non_negative(offset, "offset")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            events = self._database.get_events_by_topic(topic, limit=limit, offset=offset)
            return [self._build_event_response(str(i), e) for i, e in enumerate(events)]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get events by topic: {str(e)}"
            )

    def get_unprocessed_events(self, limit: int = 100) -> List[EventRecordResponse]:
        try:
            Preconditions.validate_range(limit, "limit", min_val=1, max_val=1000)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            events = self._database.get_unprocessed_events(limit=limit)
            return [self._build_event_response(str(i), e) for i, e in enumerate(events)]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get unprocessed events: {str(e)}"
            )

    def mark_event_processed(self, event_id: str) -> Dict[str, bool]:
        try:
            Preconditions.validate_non_empty_string(event_id, "event_id")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            success = self._database.mark_event_processed(event_id)
            Postconditions.validate_success(success, "mark_event_processed")
            return {"success": True}
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to mark event as processed: {str(e)}"
            )

    def save_consumer_offset(self, request: ConsumerOffsetRequest) -> Dict[str, bool]:
        try:
            Preconditions.validate_non_empty_string(request.consumer_group, "consumer_group")
            Preconditions.validate_non_empty_string(request.topic, "topic")
            Preconditions.validate_non_negative(request.partition, "partition")
            Preconditions.validate_non_negative(request.offset, "offset")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        offset = ConsumerOffset(
            consumer_group=request.consumer_group,
            topic=request.topic,
            partition=request.partition,
            offset=request.offset
        )

        try:
            success = self._database.save_consumer_offset(offset)
            Postconditions.validate_success(success, "save_consumer_offset")
            return {"success": True}
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save consumer offset: {str(e)}"
            )

    def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> ConsumerOffsetResponse:
        try:
            Preconditions.validate_non_empty_string(consumer_group, "consumer_group")
            Preconditions.validate_non_empty_string(topic, "topic")
            Preconditions.validate_non_negative(partition, "partition")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            offset = self._database.get_consumer_offset(consumer_group, topic, partition)
            if not offset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Consumer offset not found for group '{consumer_group}', topic '{topic}', partition {partition}. Verify the offset exists."
                )
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get consumer offset: {str(e)}"
            )

    def delete_events_by_topic(self, topic: str) -> Dict[str, int]:
        try:
            Preconditions.validate_non_empty_string(topic, "topic")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            count = self._database.delete_events_by_topic(topic)
            return {"deleted_count": count}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete events: {str(e)}"
            )

    def get_event_count(self, topic: Optional[str] = None) -> Dict[str, int]:
        try:
            count = self._database.get_event_count(topic)
            return {"count": count}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get event count: {str(e)}"
            )

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
