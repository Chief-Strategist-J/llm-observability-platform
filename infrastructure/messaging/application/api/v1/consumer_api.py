from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from fastapi import HTTPException, status, APIRouter
from pydantic import BaseModel, Field

from domain.ports.consumer_port import ConsumerPort, ConsumeParams, ParallelConsumeParams, ConsumerOffsetParams
from application.api.v1.validators import Preconditions, Postconditions, ValidationError


class ConsumeMessageRequest(BaseModel):
    topic: str = Field(..., description="Kafka topic to consume from")
    consumer_group: str = Field(..., description="Consumer group ID")
    partition: Optional[int] = Field(None, description="Specific partition (optional)")
    max_messages: int = Field(10, description="Maximum messages to consume")
    timeout_ms: int = Field(1000, description="Timeout in milliseconds")


class ConsumedMessage(BaseModel):
    topic: str
    partition: int
    offset: int
    key: Optional[str]
    value: Any
    timestamp: int
    headers: Optional[Dict[str, Any]]


class ConsumeMessageResponse(BaseModel):
    success: bool
    messages: List[ConsumedMessage]
    count: int


class ConsumerOffsetRequest(BaseModel):
    consumer_group: str = Field(..., description="Consumer group ID")
    topic: str = Field(..., description="Kafka topic")
    partition: int = Field(..., description="Partition number")
    offset: int = Field(..., description="Offset value")


class ConsumerAPI:
    def __init__(self, consumer_port: ConsumerPort):
        self._consumer = consumer_port
        self.router = APIRouter()
        self._setup_routes()

    def _supports_parallel_consume(self) -> bool:
        return hasattr(self._consumer, 'consume_parallel')

    def _supports_batch_commit(self) -> bool:
        return hasattr(self._consumer, 'commit_offsets_batch')

    def _setup_routes(self):
        @self.router.post("/consume", response_model=ConsumeMessageResponse, summary="Consume messages from Kafka")
        def consume_messages(request: ConsumeMessageRequest):
            return self._consume_messages(request)

        @self.router.post("/consume/parallel", summary="Consume messages from multiple partitions in parallel")
        def consume_parallel(topic: str, consumer_group: str, partitions: List[int], max_messages_per_partition: int = 100, timeout_ms: int = 1000):
            params = ParallelConsumeParams(topic, consumer_group, partitions, max_messages_per_partition, timeout_ms)
            return self._consume_parallel(params)

        @self.router.post("/offsets", summary="Commit consumer offset")
        def commit_offset(request: ConsumerOffsetRequest):
            return self._commit_offset(request)

        @self.router.post("/offsets/batch", summary="Commit multiple consumer offsets")
        def commit_offsets_batch(offsets: Dict[str, Dict[int, int]]):
            return self._commit_offsets_batch(offsets)

        @self.router.get("/offsets/{consumer_group}/{topic}/{partition}", summary="Get current consumer offset")
        def get_offset(consumer_group: str, topic: str, partition: int):
            return self._get_offset(consumer_group, topic, partition)

        @self.router.post("/subscribe", summary="Subscribe to a topic")
        def subscribe(topic: str, consumer_group: str):
            return self._subscribe(topic, consumer_group)

        @self.router.post("/unsubscribe", summary="Unsubscribe from a topic")
        def unsubscribe(topic: str, consumer_group: str):
            return self._unsubscribe(topic, consumer_group)

        @self.router.get("/subscriptions/{consumer_group}", summary="List subscriptions for a consumer group")
        def list_subscriptions(consumer_group: str):
            return self._list_subscriptions(consumer_group)

    def _consume_messages(self, request: ConsumeMessageRequest) -> ConsumeMessageResponse:
        try:
            Preconditions.validate_non_empty_string(request.topic, "topic")
            Preconditions.validate_non_empty_string(request.consumer_group, "consumer_group")
            Preconditions.validate_range(request.max_messages, "max_messages", min_val=1, max_val=1000)
            if request.partition is not None:
                Preconditions.validate_non_negative(request.partition, "partition")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            params = ConsumeParams(
                topic=request.topic,
                consumer_group=request.consumer_group,
                partition=request.partition,
                max_messages=request.max_messages,
                timeout_ms=request.timeout_ms
            )
            messages = self._consumer.consume(params)
            Postconditions.validate_not_none(messages, "consume")
            
            consumed_messages = [
                ConsumedMessage(
                    topic=msg.get("topic", request.topic),
                    partition=msg.get("partition", 0),
                    offset=msg.get("offset", 0),
                    key=msg.get("key"),
                    value=msg.get("value"),
                    timestamp=msg.get("timestamp", 0),
                    headers=msg.get("headers")
                )
                for msg in messages
            ]
            
            return ConsumeMessageResponse(
                success=True,
                messages=consumed_messages,
                count=len(consumed_messages)
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to consume messages: {str(e)}"
            )

    def _commit_offset(self, request: ConsumerOffsetRequest) -> Dict[str, bool]:
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
            params = ConsumerOffsetParams(
                consumer_group=request.consumer_group,
                topic=request.topic,
                partition=request.partition,
                offset=request.offset
            )
            success = self._consumer.commit_offset(params)
            Postconditions.validate_success(success, "commit_offset")
            return {"success": True}
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to commit offset: {str(e)}"
            )

    def _consume_parallel(self, params: ParallelConsumeParams) -> Dict[str, Any]:
        try:
            Preconditions.validate_non_empty_string(params.topic, "topic")
            Preconditions.validate_non_empty_string(params.consumer_group, "consumer_group")
            Preconditions.validate_not_empty_list(params.partitions, "partitions")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            if self._supports_parallel_consume():
                results = self._consumer.consume_parallel(
                    topic=params.topic,
                    consumer_group=params.consumer_group,
                    partitions=params.partitions,
                    max_messages_per_partition=params.max_messages_per_partition,
                    timeout_ms=params.timeout_ms
                )
                return {"success": True, "results": results}
            else:
                return {"success": False, "message": "Parallel consume not supported"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to consume parallel: {str(e)}"
            )

    def _commit_offsets_batch(self, offsets: Dict[str, Dict[int, int]]) -> Dict[str, bool]:
        try:
            if self._supports_batch_commit():
                results = self._consumer.commit_offsets_batch(offsets)
                return {"success": True, "results": results}
            else:
                return {"success": False, "message": "Batch commit not supported"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to commit batch offsets: {str(e)}"
            )

    def _get_offset(self, consumer_group: str, topic: str, partition: int) -> Dict[str, Any]:
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
            offset = self._consumer.get_offset(consumer_group, topic, partition)
            return {
                "consumer_group": consumer_group,
                "topic": topic,
                "partition": partition,
                "offset": offset
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get offset: {str(e)}"
            )

    def _subscribe(self, topic: str, consumer_group: str) -> Dict[str, Any]:
        try:
            Preconditions.validate_non_empty_string(topic, "topic")
            Preconditions.validate_non_empty_string(consumer_group, "consumer_group")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            result = self._consumer.subscribe(topic, consumer_group)
            Postconditions.validate_success(result, "subscribe")
            return {"success": True, "topic": topic, "consumer_group": consumer_group}
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to subscribe: {str(e)}"
            )

    def _unsubscribe(self, topic: str, consumer_group: str) -> Dict[str, Any]:
        try:
            Preconditions.validate_non_empty_string(topic, "topic")
            Preconditions.validate_non_empty_string(consumer_group, "consumer_group")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            result = self._consumer.unsubscribe(topic, consumer_group)
            Postconditions.validate_success(result, "unsubscribe")
            return {"success": True, "topic": topic, "consumer_group": consumer_group}
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to unsubscribe: {str(e)}"
            )

    def _list_subscriptions(self, consumer_group: str) -> Dict[str, List[str]]:
        try:
            Preconditions.validate_non_empty_string(consumer_group, "consumer_group")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            subscriptions = self._consumer.list_subscriptions(consumer_group)
            return {"consumer_group": consumer_group, "subscriptions": subscriptions}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list subscriptions: {str(e)}"
            )
