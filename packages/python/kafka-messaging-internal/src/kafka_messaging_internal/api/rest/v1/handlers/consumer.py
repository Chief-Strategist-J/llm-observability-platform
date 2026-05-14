"""Consumer API handlers following OpenAPI contract."""

from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status, APIRouter
from pydantic import BaseModel, Field

from infra.ports.consumer_port import ConsumerPort
from shared.types.events import ConsumeParams, ParallelConsumeParams, ConsumerOffsetParams


class ConsumeMessageRequest(BaseModel):
    """Request model for consuming messages"""
    topic: str = Field(..., description="Kafka topic to consume from")
    consumer_group: str = Field(..., description="Consumer group ID")
    partition: Optional[int] = Field(None, description="Specific partition (optional)")
    max_messages: int = Field(10, description="Maximum messages to consume")
    timeout_ms: int = Field(1000, description="Timeout in milliseconds")


class ConsumedMessage(BaseModel):
    """Response model for consumed message"""
    topic: str = Field(..., description="Topic name")
    partition: int = Field(..., description="Partition number")
    offset: int = Field(..., description="Message offset")
    key: Optional[str] = Field(None, description="Message key")
    value: Any = Field(..., description="Message value")
    timestamp: int = Field(..., description="Message timestamp")
    headers: Optional[Dict[str, Any]] = Field(None, description="Message headers")


class ConsumeMessageResponse(BaseModel):
    """Response model for consume operation"""
    success: bool = Field(..., description="Operation success status")
    messages: List[ConsumedMessage] = Field(..., description="Consumed messages")


class ParallelConsumeRequest(BaseModel):
    """Request model for parallel consumption"""
    topic: str = Field(..., description="Kafka topic to consume from")
    consumer_group: str = Field(..., description="Consumer group ID")
    partitions: List[int] = Field(..., description="Partitions to consume from")
    max_messages: int = Field(10, description="Maximum messages per partition")
    timeout_ms: int = Field(1000, description="Timeout in milliseconds")


class ParallelConsumeResponse(BaseModel):
    """Response model for parallel consume operation"""
    success: bool = Field(..., description="Operation success status")
    messages: Dict[int, List[ConsumedMessage]] = Field(..., description="Messages by partition")


class CommitOffsetRequest(BaseModel):
    """Request model for committing offsets"""
    consumer_group: str = Field(..., description="Consumer group ID")
    topic: str = Field(..., description="Topic name")
    partition: int = Field(..., description="Partition number")
    offset: int = Field(..., description="Offset to commit")


class SubscribeRequest(BaseModel):
    """Request model for subscribing to topics"""
    topics: List[str] = Field(..., description="Topics to subscribe to")


class ConsumerAPI:
    """REST API handlers for consumer operations"""
    
    def __init__(self, consumer: ConsumerPort):
        self._consumer = consumer
        self.router = APIRouter()

    def _setup_routes(self):
        """Setup API routes"""
        
        @self.router.post("/consume", response_model=ConsumeMessageResponse)
        async def consume_messages(request: ConsumeMessageRequest) -> ConsumeMessageResponse:
            """Consume messages from topic"""
            try:
                params = ConsumeParams(
                    topic=request.topic,
                    partition=request.partition,
                    max_messages=request.max_messages,
                    timeout=request.timeout_ms / 1000  # Convert to seconds
                )
                
                messages_data = self._consumer.consume(params)
                
                messages = [
                    ConsumedMessage(
                        topic=msg['topic'],
                        partition=msg['partition'],
                        offset=msg['offset'],
                        key=msg['key'],
                        value=msg['value'],
                        timestamp=msg['timestamp'],
                        headers=msg['headers']
                    )
                    for msg in messages_data
                ]
                
                return ConsumeMessageResponse(
                    success=True,
                    messages=messages
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.post("/consume/parallel", response_model=ParallelConsumeResponse)
        async def consume_parallel(request: ParallelConsumeRequest) -> ParallelConsumeResponse:
            """Consume messages from multiple partitions in parallel"""
            try:
                params = ParallelConsumeParams(
                    topic=request.topic,
                    partitions=request.partitions,
                    max_messages=request.max_messages,
                    timeout=request.timeout_ms / 1000
                )
                
                messages_data = self._consumer.consume_parallel(params)
                
                messages_by_partition = {}
                for partition, msgs in messages_data.items():
                    messages_by_partition[partition] = [
                        ConsumedMessage(
                            topic=msg['topic'],
                            partition=msg['partition'],
                            offset=msg['offset'],
                            key=msg['key'],
                            value=msg['value'],
                            timestamp=msg['timestamp'],
                            headers=msg['headers']
                        )
                        for msg in msgs
                    ]
                
                return ParallelConsumeResponse(
                    success=True,
                    messages=messages_by_partition
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.post("/commit", response_model=dict)
        async def commit_offsets() -> dict:
            """Commit current offsets"""
            try:
                self._consumer.commit()
                return {"success": True}
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.post("/commit/offset", response_model=dict)
        async def commit_offset(request: CommitOffsetRequest) -> dict:
            """Commit specific offset"""
            try:
                params = ConsumerOffsetParams(
                    consumer_group=request.consumer_group,
                    topic=request.topic,
                    partition=request.partition,
                    offset=request.offset
                )
                
                self._consumer.commit_offset(params)
                return {"success": True}
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.post("/subscribe", response_model=dict)
        async def subscribe_topics(request: SubscribeRequest) -> dict:
            """Subscribe to topics"""
            try:
                self._consumer.subscribe(request.topics)
                return {"success": True, "topics": request.topics}
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.post("/unsubscribe", response_model=dict)
        async def unsubscribe_topics() -> dict:
            """Unsubscribe from all topics"""
            try:
                self._consumer.unsubscribe()
                return {"success": True}
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

    def get_router(self) -> APIRouter:
        """Get configured router"""
        self._setup_routes()
        return self.router
