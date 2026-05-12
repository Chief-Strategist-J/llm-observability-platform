"""Producer API handlers following OpenAPI contract."""

from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status, APIRouter
from pydantic import BaseModel, Field

from infra.ports.producer_port import ProducerPort
from shared.types.events import ProduceMessageParams, TopicCreationParams


class ProduceMessageRequest(BaseModel):
    """Request model for producing messages"""
    topic: str = Field(..., description="Kafka topic to produce to")
    key: Optional[str] = Field(None, description="Message key")
    value: Any = Field(..., description="Message value (any JSON-serializable type)")
    partition: Optional[int] = Field(None, description="Specific partition (optional)")
    headers: Optional[Dict[str, Any]] = Field(None, description="Message headers")


class ProduceMessageResponse(BaseModel):
    """Response model for produced message"""
    success: bool = Field(..., description="Operation success status")
    topic: str = Field(..., description="Topic name")
    partition: int = Field(..., description="Partition number")
    offset: int = Field(..., description="Message offset")
    key: Optional[str] = Field(None, description="Message key")
    timestamp: int = Field(..., description="Message timestamp")


class BatchProduceMessageRequest(BaseModel):
    """Request model for batch message production"""
    messages: List[ProduceMessageRequest] = Field(..., description="List of messages to produce")


class BatchProduceMessageResponse(BaseModel):
    """Response model for batch message production"""
    success: bool = Field(..., description="Operation success status")
    results: List[ProduceMessageResponse] = Field(..., description="Results for each message")
    count: int = Field(..., description="Number of messages produced")


class TopicCreationRequest(BaseModel):
    """Request model for topic creation"""
    topic_name: str = Field(..., description="Topic name")
    partitions: int = Field(1, description="Number of partitions")
    replication_factor: int = Field(1, description="Replication factor")


class ProducerAPI:
    """REST API handlers for producer operations"""
    
    def __init__(self, producer: ProducerPort):
        self._producer = producer
        self.router = APIRouter()

    def _setup_routes(self):
        """Setup API routes"""
        
        @self.router.post("/produce", response_model=ProduceMessageResponse)
        async def produce_message(request: ProduceMessageRequest) -> ProduceMessageResponse:
            """Produce a single message"""
            try:
                params = ProduceMessageParams(
                    topic=request.topic,
                    key=request.key,
                    value=request.value,
                    partition=request.partition,
                    headers=request.headers
                )
                
                result = self._producer.produce(params)
                
                return ProduceMessageResponse(
                    success=True,
                    topic=result['topic'],
                    partition=result['partition'],
                    offset=result['offset'],
                    key=request.key,
                    timestamp=result.get('timestamp', 0)
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.post("/produce/batch", response_model=BatchProduceMessageResponse)
        async def produce_batch(request: BatchProduceMessageRequest) -> BatchProduceMessageResponse:
            """Produce multiple messages in batch"""
            try:
                params_list = [
                    ProduceMessageParams(
                        topic=msg.topic,
                        key=msg.key,
                        value=msg.value,
                        partition=msg.partition,
                        headers=msg.headers
                    )
                    for msg in request.messages
                ]
                
                results = self._producer.produce_batch(request.topic, params_list)
                
                response_results = [
                    ProduceMessageResponse(
                        success=True,
                        topic=result['topic'],
                        partition=result['partition'],
                        offset=result['offset'],
                        key=msg.key,
                        timestamp=result.get('timestamp', 0)
                    )
                    for result, msg in zip(results, request.messages)
                ]
                
                return BatchProduceMessageResponse(
                    success=True,
                    results=response_results,
                    count=len(response_results)
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.post("/flush", response_model=dict)
        async def flush_producer() -> dict:
            """Flush pending messages"""
            try:
                self._producer.flush()
                return {"success": True}
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.get("/topics", response_model=List[str])
        async def list_topics() -> List[str]:
            """List available topics"""
            try:
                topics = self._producer.list_topics()
                return topics
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.post("/topics", response_model=dict)
        async def create_topic(request: TopicCreationRequest) -> dict:
            """Create a new topic"""
            try:
                params = TopicCreationParams(
                    topic_name=request.topic_name,
                    partitions=request.partitions,
                    replication_factor=request.replication_factor
                )
                
                success = self._producer.create_topic(params)
                
                return {
                    "success": success,
                    "topic_name": request.topic_name,
                    "partitions": request.partitions,
                    "replication_factor": request.replication_factor
                }
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

    def get_router(self) -> APIRouter:
        """Get configured router"""
        self._setup_routes()
        return self.router
