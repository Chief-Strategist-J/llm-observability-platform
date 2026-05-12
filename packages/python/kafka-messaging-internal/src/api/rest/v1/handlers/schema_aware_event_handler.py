"""Schema-Aware Event Handler API handlers following OpenAPI contract."""

from typing import Any, Dict, List
from fastapi import HTTPException, status, APIRouter
from pydantic import BaseModel, Field

from features.schema_aware_events.service import SchemaAwareEventService


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


class SchemaAwareEventHandlerAPI:
    """REST API handlers for schema-aware event processing operations"""
    
    def __init__(self, schema_aware_event_service: SchemaAwareEventService):
        self._schema_aware_event_service = schema_aware_event_service
        self.router = APIRouter()

    def _setup_routes(self):
        """Setup API routes"""
        
        @self.router.post("/process")
        async def process_event(
            request: ConsumerRecordRequest,
            deserialize: bool = Field(True, description="Whether to deserialize the value")
        ) -> Dict[str, Any]:
            """Process a single consumer record with optional deserialization"""
            try:
                record_dict = request.dict()
                event_id = await self._schema_aware_event_service.process_kafka_record(
                    record_dict, deserialize
                )
                return {
                    "event_id": event_id,
                    "success": True,
                    "result": {"stored": True, "deserialized": deserialize}
                }
            except Exception as e:
                return {
                    "event_id": None,
                    "success": False,
                    "error": str(e)
                }

        @self.router.post("/process/batch")
        async def process_events_batch(
            request: BatchConsumerRecordRequest,
            deserialize: bool = Field(True, description="Whether to deserialize the values")
        ) -> Dict[str, Any]:
            """Process multiple consumer records in batch with optional deserialization"""
            try:
                records = [record.dict() for record in request.records]
                event_ids = await self._schema_aware_event_service.process_kafka_records_batch(
                    records, deserialize
                )
                return {
                    "event_ids": event_ids,
                    "count": len(event_ids),
                    "success": True,
                    "deserialized": deserialize
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
