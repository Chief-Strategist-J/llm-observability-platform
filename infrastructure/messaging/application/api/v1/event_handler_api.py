from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import HTTPException, status, APIRouter
from pydantic import BaseModel, Field

from domain.ports.event_handler_port import EventHandlerPort
from application.api.v1.validators import Preconditions, Postconditions, ValidationError


class ConsumerRecordRequest(BaseModel):
    topic: str = Field(..., description="Kafka topic name")
    partition: int = Field(..., description="Kafka partition number")
    offset: int = Field(..., description="Kafka message offset")
    key: Optional[str] = Field(None, description="Message key")
    value: Any = Field(..., description="Message value (any JSON-serializable type)")
    timestamp: int = Field(..., description="Kafka timestamp (milliseconds since epoch)")
    headers: Optional[Dict[str, Any]] = Field(None, description="Message headers")


class BatchConsumerRecordRequest(BaseModel):
    records: List[ConsumerRecordRequest] = Field(..., description="List of consumer records")


class ProcessEventResponse(BaseModel):
    event_id: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None


class BatchProcessEventResponse(BaseModel):
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


class SubjectMappingRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="Kafka topic name")
    subject: str = Field(..., min_length=1, description="Schema registry subject name")


class UnprocessedProcessRequest(BaseModel):
    batch_size: int = Field(100, ge=1, le=1000, description="Number of unprocessed events to process")


class UnprocessedProcessResponse(BaseModel):
    results: List[Dict[str, Any]]
    count: int
    success: bool


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


class EventHandlerAPI:
    def __init__(self, event_handler):
        self._event_handler = event_handler
        self.router = APIRouter()
        self._setup_routes()

    def _serialize_datetime(self, dt: Any) -> str:
        if isinstance(dt, datetime):
            return dt.isoformat()
        return str(dt)

    def _setup_routes(self):
        @self.router.post("/process-record", response_model=ProcessEventResponse)
        def process_record_route(request: ConsumerRecordRequest):
            return self.process_record(request)

        @self.router.post("/process-records-batch", response_model=BatchProcessEventResponse)
        def process_records_batch_route(request: BatchConsumerRecordRequest):
            return self.process_records_batch(request)

        @self.router.post("/consumer-offsets")
        def save_consumer_offset_route(request: ConsumerOffsetRequest):
            return self.save_consumer_offset(request)

        @self.router.get("/consumer-offsets/{consumer_group}/{topic}/{partition}")
        def get_consumer_offset_route(consumer_group: str, topic: str, partition: int):
            return self.get_consumer_offset(consumer_group, topic, partition)

        @self.router.get("/events")
        def get_events_by_topic_route(topic: str, limit: int = 100, offset: int = 0):
            return self.get_events_by_topic(topic, limit, offset)

        @self.router.get("/events/{topic}/count")
        def get_event_count_route(topic: str):
            return self.get_event_count(topic)

    def process_record(self, request: ConsumerRecordRequest) -> ProcessEventResponse:
        try:
            Preconditions.validate_non_empty_string(request.topic, "topic")
            Preconditions.validate_non_negative(request.partition, "partition")
            Preconditions.validate_non_negative(request.offset, "offset")
            Preconditions.validate_non_negative(request.timestamp, "timestamp")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            record = ConsumerRecord(
                topic=request.topic,
                partition=request.partition,
                offset=request.offset,
                key=request.key,
                value=request.value,
                timestamp=request.timestamp,
                headers=request.headers
            )
            event_id = self._event_handler.process_kafka_record(record)
            Preconditions.validate_not_none(event_id, "process_kafka_record")
            return ProcessEventResponse(
                event_id=event_id,
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
                detail=f"Failed to process record: {str(e)}"
            )

    def process_records_batch(self, request: BatchConsumerRecordRequest) -> BatchProcessEventResponse:
        try:
            Preconditions.validate_list_size(request.records, "records", min_size=1, max_size=1000)
            for record in request.records:
                Preconditions.validate_non_empty_string(record.topic, "topic")
                Preconditions.validate_non_negative(record.partition, "partition")
                Preconditions.validate_non_negative(record.offset, "offset")
                Preconditions.validate_non_negative(record.timestamp, "timestamp")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            records = [
                ConsumerRecord(
                    topic=r.topic,
                    partition=r.partition,
                    offset=r.offset,
                    key=r.key,
                    value=r.value,
                    timestamp=r.timestamp,
                    headers=r.headers
                )
                for r in request.records
            ]
            event_ids = self._event_handler.process_kafka_records_batch(records)
            Preconditions.validate_not_none(event_ids, "process_kafka_records_batch")
            Preconditions.validate_not_empty_list(event_ids, "process_kafka_records_batch")
            return BatchProcessEventResponse(
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
                detail=f"Failed to process records batch: {str(e)}"
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

        try:
            success = self._event_handler.save_consumer_offset(
                request.consumer_group,
                request.topic,
                request.partition,
                request.offset
            )
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
            offset = self._event_handler.get_consumer_offset(consumer_group, topic, partition)
            if offset is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Consumer offset not found for group '{consumer_group}', topic '{topic}', partition {partition}. Verify the offset exists."
                )
            return ConsumerOffsetResponse(
                consumer_group=consumer_group,
                topic=topic,
                partition=partition,
                offset=offset
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get consumer offset: {str(e)}"
            )

    def get_events_by_topic(self, topic: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
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
            events = self._event_handler.get_events_by_topic(topic, limit=limit, offset=offset)
            return [
                {
                    "topic": e.topic,
                    "partition": e.partition,
                    "offset": e.offset,
                    "key": e.key,
                    "value": e.value,
                    "timestamp": self._serialize_datetime(e.timestamp),
                    "headers": e.headers,
                    "processed": e.processed,
                    "error": e.error,
                    "created_at": self._serialize_datetime(e.created_at)
                }
                for e in events
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get events by topic: {str(e)}"
            )

    def get_event_count(self, topic: Optional[str] = None) -> Dict[str, int]:
        try:
            count = self._event_handler.get_event_count(topic)
            return {"count": count}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get event count: {str(e)}"
            )


class SchemaAwareEventHandlerAPI:
    def __init__(self, schema_aware_event_handler):
        self._handler = schema_aware_event_handler
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        @self.router.post("/register-subject-mapping")
        def register_subject_mapping_route(request: SubjectMappingRequest):
            return self.register_subject_mapping(request)

        @self.router.post("/process-record", response_model=ProcessEventResponse)
        def process_record_route(request: ConsumerRecordRequest, deserialize: bool = True):
            return self.process_record(request, deserialize)

        @self.router.post("/process-records-batch", response_model=BatchProcessEventResponse)
        def process_records_batch_route(request: BatchConsumerRecordRequest, deserialize: bool = True):
            return self.process_records_batch(request, deserialize)

        @self.router.post("/serialize-and-produce")
        def serialize_and_produce_route(request: SerializationRequest):
            return self.serialize_and_produce(request)

        @self.router.post("/consumer-offsets")
        def save_consumer_offset_route(request: ConsumerOffsetRequest):
            return self.save_consumer_offset(request)

        @self.router.get("/consumer-offsets/{consumer_group}/{topic}/{partition}")
        def get_consumer_offset_route(consumer_group: str, topic: str, partition: int):
            return self.get_consumer_offset(consumer_group, topic, partition)

        @self.router.get("/registered-subjects")
        def list_registered_subjects_route():
            return self.list_registered_subjects()

    def register_subject_mapping(self, request: SubjectMappingRequest) -> Dict[str, bool]:
        try:
            Preconditions.validate_non_empty_string(request.topic, "topic")
            Preconditions.validate_non_empty_string(request.subject, "subject")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            self._handler.register_subject_mapping(request.topic, request.subject)
            return {"success": True}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to register subject mapping: {str(e)}"
            )

    def process_record(self, request: ConsumerRecordRequest, deserialize: bool = True) -> ProcessEventResponse:
        try:
            Preconditions.validate_non_empty_string(request.topic, "topic")
            Preconditions.validate_non_negative(request.partition, "partition")
            Preconditions.validate_non_negative(request.offset, "offset")
            Preconditions.validate_non_negative(request.timestamp, "timestamp")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            record = ConsumerRecord(
                topic=request.topic,
                partition=request.partition,
                offset=request.offset,
                key=request.key,
                value=request.value,
                timestamp=request.timestamp,
                headers=request.headers
            )
            event_id = self._handler.process_kafka_record(record, deserialize=deserialize)
            Preconditions.validate_not_none(event_id, "process_kafka_record")
            return ProcessEventResponse(
                event_id=event_id,
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
                detail=f"Failed to process record: {str(e)}"
            )

    def process_records_batch(self, request: BatchConsumerRecordRequest, deserialize: bool = True) -> BatchProcessEventResponse:
        try:
            Preconditions.validate_list_size(request.records, "records", min_size=1, max_size=1000)
            for record in request.records:
                Preconditions.validate_non_empty_string(record.topic, "topic")
                Preconditions.validate_non_negative(record.partition, "partition")
                Preconditions.validate_non_negative(record.offset, "offset")
                Preconditions.validate_non_negative(record.timestamp, "timestamp")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            records = [
                ConsumerRecord(
                    topic=r.topic,
                    partition=r.partition,
                    offset=r.offset,
                    key=r.key,
                    value=r.value,
                    timestamp=r.timestamp,
                    headers=r.headers
                )
                for r in request.records
            ]
            event_ids = self._handler.process_kafka_records_batch(records, deserialize=deserialize)
            Preconditions.validate_not_none(event_ids, "process_kafka_records_batch")
            Preconditions.validate_not_empty_list(event_ids, "process_kafka_records_batch")
            return BatchProcessEventResponse(
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
                detail=f"Failed to process records batch: {str(e)}"
            )

    def serialize_and_produce(self, topic: str, data: Any, subject: Optional[str] = None) -> Dict[str, str]:
        try:
            Preconditions.validate_non_empty_string(topic, "topic")
            Preconditions.validate_not_none(data, "data")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            serialized = self._handler.serialize_and_produce(topic, data, subject)
            Preconditions.validate_not_none(serialized, "serialize_and_produce")
            import base64
            return {"data": base64.b64encode(serialized).decode('utf-8')}
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to serialize and produce: {str(e)}"
            )

    def list_registered_subjects(self) -> Dict[str, List[str]]:
        try:
            subjects = self._handler.list_registered_subjects()
            return {"subjects": subjects}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list registered subjects: {str(e)}"
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

        try:
            success = self._handler.save_consumer_offset(
                request.consumer_group,
                request.topic,
                request.partition,
                request.offset
            )
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
            offset = self._handler.get_consumer_offset(consumer_group, topic, partition)
            if offset is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Consumer offset not found for group '{consumer_group}', topic '{topic}', partition {partition}. Verify the offset exists."
                )
            return ConsumerOffsetResponse(
                consumer_group=consumer_group,
                topic=topic,
                partition=partition,
                offset=offset
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get consumer offset: {str(e)}"
            )
