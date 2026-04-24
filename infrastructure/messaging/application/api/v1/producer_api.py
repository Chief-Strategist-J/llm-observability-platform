from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status, APIRouter
from pydantic import BaseModel, Field
import asyncio

from infrastructure.messaging.domain.ports.producer_port import ProducerPort
from infrastructure.messaging.application.api.v1.validators import Preconditions, Postconditions, ValidationError


class ProduceMessageRequest(BaseModel):
    topic: str = Field(..., description="Kafka topic to produce to")
    key: Optional[str] = Field(None, description="Message key")
    value: Any = Field(..., description="Message value (any JSON-serializable type)")
    partition: Optional[int] = Field(None, description="Specific partition (optional)")
    headers: Optional[Dict[str, Any]] = Field(None, description="Message headers")


class ProduceMessageResponse(BaseModel):
    success: bool
    topic: str
    partition: int
    offset: int
    key: Optional[str]
    timestamp: int


class BatchProduceMessageRequest(BaseModel):
    messages: List[ProduceMessageRequest] = Field(..., description="List of messages to produce")


class BatchProduceMessageResponse(BaseModel):
    success: bool
    count: int
    results: List[ProduceMessageResponse]


class ProducerAPI:
    def __init__(self, producer_port: ProducerPort):
        self._producer = producer_port
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        @self.router.post("/produce", response_model=ProduceMessageResponse, summary="Produce a single message to Kafka")
        def produce_message(request: ProduceMessageRequest):
            return self._produce_message(request)

        @self.router.post("/produce/batch", response_model=BatchProduceMessageResponse, summary="Produce multiple messages to Kafka")
        def produce_messages_batch(request: BatchProduceMessageRequest):
            return self._produce_messages_batch(request)

        @self.router.post("/produce/async", summary="Produce message asynchronously")
        async def produce_message_async(request: ProduceMessageRequest):
            return await self._produce_message_async(request)

        @self.router.post("/flush", summary="Flush buffered messages")
        def flush_producer():
            return self._flush()

        @self.router.get("/topics", summary="List available topics")
        def list_topics():
            return self._list_topics()

        @self.router.post("/topics/{topic_name}", summary="Create a new topic")
        def create_topic(topic_name: str, partitions: int = 1, replication_factor: int = 1):
            return self._create_topic(topic_name, partitions, replication_factor)

    def _produce_message(self, request: ProduceMessageRequest) -> ProduceMessageResponse:
        try:
            Preconditions.validate_non_empty_string(request.topic, "topic")
            if request.partition is not None:
                Preconditions.validate_non_negative(request.partition, "partition")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            result = self._producer.produce(
                topic=request.topic,
                key=request.key,
                value=request.value,
                partition=request.partition,
                headers=request.headers
            )
            Postconditions.validate_not_none(result, "produce")
            
            return ProduceMessageResponse(
                success=True,
                topic=result.get("topic", request.topic),
                partition=result.get("partition", 0),
                offset=result.get("offset", 0),
                key=request.key,
                timestamp=result.get("timestamp", 0)
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to produce message: {str(e)}"
            )

    def _produce_messages_batch(self, request: BatchProduceMessageRequest) -> BatchProduceMessageResponse:
        try:
            Preconditions.validate_list_size(request.messages, "messages", min_size=1, max_size=10000)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            messages_data = [
                {
                    "topic": msg.topic,
                    "key": msg.key,
                    "value": msg.value,
                    "partition": msg.partition,
                    "headers": msg.headers
                }
                for msg in request.messages
            ]
            
            if hasattr(self._producer, 'produce_batch'):
                results = self._producer.produce_batch(request.messages[0].topic, messages_data)
            else:
                results = []
                for msg in request.messages:
                    result = self._producer.produce(
                        topic=msg.topic,
                        key=msg.key,
                        value=msg.value,
                        partition=msg.partition,
                        headers=msg.headers
                    )
                    results.append(result)
            
            return BatchProduceMessageResponse(
                success=True,
                count=len(results),
                results=[
                    ProduceMessageResponse(
                        success=True,
                        topic=r.get("topic", ""),
                        partition=r.get("partition", 0),
                        offset=r.get("offset", 0),
                        key=r.get("key"),
                        timestamp=r.get("timestamp", 0)
                    )
                    for r in results
                ]
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to produce batch messages: {str(e)}"
            )

    async def _produce_message_async(self, request: ProduceMessageRequest) -> ProduceMessageResponse:
        try:
            Preconditions.validate_non_empty_string(request.topic, "topic")
            if request.partition is not None:
                Preconditions.validate_non_negative(request.partition, "partition")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            if hasattr(self._producer, 'produce_async'):
                future = self._producer.produce_async(
                    topic=request.topic,
                    key=request.key,
                    value=request.value,
                    partition=request.partition,
                    headers=request.headers
                )
                result = await asyncio.wrap_future(future)
            else:
                result = self._producer.produce(
                    topic=request.topic,
                    key=request.key,
                    value=request.value,
                    partition=request.partition,
                    headers=request.headers
                )
            
            return ProduceMessageResponse(
                success=True,
                topic=result.get("topic", request.topic),
                partition=result.get("partition", 0),
                offset=result.get("offset", 0),
                key=request.key,
                timestamp=result.get("timestamp", 0)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to produce message async: {str(e)}"
            )

    def _flush(self) -> Dict[str, bool]:
        try:
            if hasattr(self._producer, 'flush'):
                self._producer.flush()
            return {"success": True}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to flush producer: {str(e)}"
            )

    def _list_topics(self) -> Dict[str, List[str]]:
        try:
            topics = self._producer.list_topics()
            Postconditions.validate_not_none(topics, "list_topics")
            return {"topics": topics}
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list topics: {str(e)}"
            )

    def _create_topic(self, topic_name: str, partitions: int, replication_factor: int) -> Dict[str, Any]:
        try:
            Preconditions.validate_non_empty_string(topic_name, "topic_name")
            Preconditions.validate_positive(partitions, "partitions")
            Preconditions.validate_positive(replication_factor, "replication_factor")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            result = self._producer.create_topic(topic_name, partitions, replication_factor)
            Postconditions.validate_success(result, "create_topic")
            return {"success": True, "topic": topic_name}
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create topic: {str(e)}"
            )
