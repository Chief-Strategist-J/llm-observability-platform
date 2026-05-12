"""Database API handlers following OpenAPI contract."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import HTTPException, status, APIRouter, Depends, Query
from pydantic import BaseModel, Field

from infra.ports.database_port import DatabasePort
from shared.types.events import EventRecord, ConsumerOffset


class EventRecordRequest(BaseModel):
    """Request model for storing an event"""
    event_id: Optional[str] = Field(None, description="Unique event identifier for idempotency")
    topic: str = Field(..., description="Kafka topic name")
    partition: int = Field(..., description="Kafka partition number")
    offset: int = Field(..., description="Kafka message offset")
    key: Optional[str] = Field(None, description="Message key")
    value: Any = Field(..., description="Message value (any JSON-serializable type)")
    timestamp: Optional[datetime] = Field(None, description="Event timestamp")


class BatchEventRequest(BaseModel):
    """Request model for storing multiple events"""
    events: List[EventRecordRequest] = Field(..., min_items=1, max_items=1000)


class ConsumerOffsetRequest(BaseModel):
    """Request model for updating consumer offset"""
    consumer_group: str = Field(..., description="Consumer group name")
    topic: str = Field(..., description="Kafka topic name")
    partition: int = Field(..., description="Kafka partition number")
    offset: int = Field(..., description="Consumer offset value")


class DatabaseAPI:
    """REST API handlers for database operations"""
    
    def __init__(self, database: DatabasePort):
        self._database = database
        self.router = APIRouter()

    def _setup_routes(self):
        """Setup API routes"""
        
        @self.router.post("/events", status_code=status.HTTP_201_CREATED)
        async def store_event(request: EventRecordRequest) -> Dict[str, Any]:
            """Store a single event in database"""
            try:
                event = EventRecord(
                    topic=request.topic,
                    partition=request.partition,
                    offset=request.offset,
                    key=request.key,
                    value=request.value,
                    timestamp=request.timestamp or datetime.utcnow(),
                    event_id=request.event_id
                )
                event_id = self._database.save_event(event)
                return {"event_id": event_id, "success": True}
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.get("/events")
        async def query_events(
            topic: Optional[str] = Query(None, description="Filter by topic name"),
            partition: Optional[int] = Query(None, description="Filter by partition number"),
            offset_from: Optional[int] = Query(None, description="Start offset (inclusive)"),
            offset_to: Optional[int] = Query(None, description="End offset (inclusive)"),
            limit: int = Query(100, ge=1, le=1000, description="Maximum number of events")
        ) -> Dict[str, Any]:
            """Query events from database"""
            try:
                # This is a simplified implementation - real implementation would use all query params
                events = self._database.get_events_by_topic(topic or "", limit=limit, offset=offset_from or 0)
                return {
                    "events": events,
                    "count": len(events),
                    "has_more": len(events) == limit
                }
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.post("/events/batch", status_code=status.HTTP_201_CREATED)
        async def store_events_batch(request: BatchEventRequest) -> Dict[str, Any]:
            """Store multiple events in batch"""
            try:
                events = [
                    EventRecord(
                        topic=event.topic,
                        partition=event.partition,
                        offset=event.offset,
                        key=event.key,
                        value=event.value,
                        timestamp=event.timestamp or datetime.utcnow(),
                        event_id=event.event_id
                    )
                    for event in request.events
                ]
                event_ids = self._database.save_events_batch(events)
                return {
                    "event_ids": event_ids,
                    "count": len(event_ids),
                    "success": True
                }
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.get("/offsets")
        async def get_consumer_offsets(
            consumer_group: str = Query(..., description="Consumer group name"),
            topic: Optional[str] = Query(None, description="Filter by topic name")
        ) -> Dict[str, Any]:
            """Get consumer offsets"""
            try:
                # Simplified implementation - real implementation would handle topic filtering
                offsets = []  # Would query database for offsets
                return {"offsets": offsets}
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.post("/offsets")
        async def update_consumer_offset(request: ConsumerOffsetRequest) -> Dict[str, Any]:
            """Update consumer offset"""
            try:
                offset = ConsumerOffset(
                    consumer_group=request.consumer_group,
                    topic=request.topic,
                    partition=request.partition,
                    offset=request.offset
                )
                success = self._database.save_consumer_offset(offset)
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Consumer offset not found"
                    )
                return {
                    "consumer_group": request.consumer_group,
                    "topic": request.topic,
                    "partition": request.partition,
                    "offset": request.offset
                }
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

    def get_router(self) -> APIRouter:
        """Get configured router"""
        self._setup_routes()
        return self.router
