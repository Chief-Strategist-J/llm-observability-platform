"""Event Handler API handlers following OpenAPI contract."""

from typing import Any, Dict, List
from fastapi import HTTPException, status, APIRouter
from pydantic import BaseModel, Field

from features.events.service import EventService


class ConsumerRecordRequest(BaseModel):
    """Request model for processing a consumer record"""
    topic: str = Field(..., description="Kafka topic name")
    partition: int = Field(..., description="Kafka partition number")
    offset: int = Field(..., description="Kafka message offset")
    key: Any = Field(None, description="Message key")
    value: Any = Field(..., description="Message value (any JSON-serializable type)")
    timestamp: int = Field(..., description="Kafka timestamp (milliseconds since epoch)")
    headers: Dict[str, Any] = Field(None, description="Message headers")


class BatchConsumerRecordRequest(BaseModel):
    """Request model for processing multiple consumer records"""
    records: List[ConsumerRecordRequest] = Field(..., min_items=1, max_items=1000)


class EventHandlerAPI:
    """REST API handlers for event processing operations"""
    
    def __init__(self, event_service: EventService):
        self._event_service = event_service
        self.router = APIRouter()

    def _setup_routes(self):
        """Setup API routes"""
        
        @self.router.post("/process")
        async def process_event(request: ConsumerRecordRequest) -> Dict[str, Any]:
            """Process a single consumer record"""
            try:
                record_dict = request.dict()
                event_id = await self._event_service.process_kafka_record(record_dict)
                return {
                    "event_id": event_id,
                    "success": True,
                    "result": {"stored": True}
                }
            except Exception as e:
                return {
                    "event_id": None,
                    "success": False,
                    "error": str(e)
                }

        @self.router.post("/process/batch")
        async def process_events_batch(request: BatchConsumerRecordRequest) -> Dict[str, Any]:
            """Process multiple consumer records in batch"""
            try:
                records = [record.dict() for record in request.records]
                event_ids = await self._event_service.process_kafka_records_batch(records)
                return {
                    "event_ids": event_ids,
                    "count": len(event_ids),
                    "success": True
                }
            except Exception as e:
                return {
                    "event_ids": [],
                    "count": 0,
                    "success": False,
                    "error": str(e)
                }

    def get_router(self) -> APIRouter:
        """Get configured router"""
        self._setup_routes()
        return self.router
