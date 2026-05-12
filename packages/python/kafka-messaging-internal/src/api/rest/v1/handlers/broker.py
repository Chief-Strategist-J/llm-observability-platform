"""Broker API handlers following OpenAPI contract."""

from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status, APIRouter
from pydantic import BaseModel, Field

from infra.ports.producer_port import ProducerPort
from infra.ports.consumer_port import ConsumerPort


class BrokerMetadataResponse(BaseModel):
    """Response model for broker metadata"""
    cluster_id: str = Field(..., description="Cluster identifier")
    controller_id: int = Field(..., description="Controller ID")
    broker_count: int = Field(..., description="Number of brokers")
    topic_count: int = Field(..., description="Number of topics")


class BrokerInfoResponse(BaseModel):
    """Response model for broker information"""
    broker_id: int = Field(..., description="Broker ID")
    host: str = Field(..., description="Broker hostname")
    port: int = Field(..., description="Broker port")
    rack: Optional[str] = Field(None, description="Broker rack")


class TopicMetadataResponse(BaseModel):
    """Response model for topic metadata"""
    topic_name: str = Field(..., description="Topic name")
    partition_count: int = Field(..., description="Number of partitions")
    replication_factor: int = Field(..., description="Replication factor")
    partitions: List[Dict[str, Any]] = Field(..., description="Partition details")


class ConsumerGroupResponse(BaseModel):
    """Response model for consumer group information"""
    group_id: str = Field(..., description="Consumer group ID")
    state: str = Field(..., description="Group state")
    members: List[Dict[str, Any]] = Field(..., description="Group members")


class BrokerAPI:
    """REST API handlers for broker operations"""
    
    def __init__(self, producer: ProducerPort, consumer: ConsumerPort):
        self._producer = producer
        self._consumer = consumer
        self.router = APIRouter()

    def _setup_routes(self):
        """Setup API routes"""
        
        @self.router.get("/metadata", response_model=BrokerMetadataResponse)
        async def get_cluster_metadata() -> BrokerMetadataResponse:
            """Get cluster metadata"""
            try:
                # Get cluster metadata from producer
                topics = self._producer.list_topics()
                
                return BrokerMetadataResponse(
                    cluster_id="kafka-cluster-1",
                    controller_id=1,
                    broker_count=3,
                    topic_count=len(topics)
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.get("/brokers", response_model=List[BrokerInfoResponse])
        async def get_brokers() -> List[BrokerInfoResponse]:
            """Get broker information"""
            try:
                # Simplified broker info - would get from cluster metadata
                brokers = [
                    BrokerInfoResponse(
                        broker_id=1,
                        host="localhost",
                        port=9092,
                        rack="rack1"
                    ),
                    BrokerInfoResponse(
                        broker_id=2,
                        host="localhost",
                        port=9093,
                        rack="rack2"
                    ),
                    BrokerInfoResponse(
                        broker_id=3,
                        host="localhost",
                        port=9094,
                        rack="rack3"
                    )
                ]
                return brokers
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.get("/topics", response_model=List[str])
        async def get_topics() -> List[str]:
            """List all topics"""
            try:
                topics = self._producer.list_topics()
                return topics
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.get("/topics/{topic_name}", response_model=TopicMetadataResponse)
        async def get_topic_metadata(topic_name: str) -> TopicMetadataResponse:
            """Get topic metadata"""
            try:
                # Simplified topic metadata
                partitions = [
                    {
                        "partition": 0,
                        "leader": 1,
                        "replicas": [1, 2, 3],
                        "isr": [1, 2, 3]
                    },
                    {
                        "partition": 1,
                        "leader": 2,
                        "replicas": [1, 2, 3],
                        "isr": [1, 2, 3]
                    }
                ]
                
                return TopicMetadataResponse(
                    topic_name=topic_name,
                    partition_count=len(partitions),
                    replication_factor=3,
                    partitions=partitions
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.get("/consumer-groups", response_model=List[ConsumerGroupResponse])
        async def get_consumer_groups() -> List[ConsumerGroupResponse]:
            """List consumer groups"""
            try:
                # Simplified consumer group info
                groups = [
                    ConsumerGroupResponse(
                        group_id="test-group-1",
                        state="Stable",
                        members=[
                            {
                                "consumer_id": "consumer-1",
                                "host": "localhost",
                                "assignment": [
                                    {"topic": "test-topic", "partitions": [0]}
                                ]
                            }
                        ]
                    )
                ]
                return groups
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.router.get("/consumer-groups/{group_id}", response_model=ConsumerGroupResponse)
        async def get_consumer_group(group_id: str) -> ConsumerGroupResponse:
            """Get specific consumer group"""
            try:
                # Simplified consumer group info
                group = ConsumerGroupResponse(
                    group_id=group_id,
                    state="Stable",
                    members=[
                        {
                            "consumer_id": "consumer-1",
                            "host": "localhost",
                            "assignment": [
                                {"topic": "test-topic", "partitions": [0]}
                            ]
                        }
                    ]
                )
                return group
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

    def get_router(self) -> APIRouter:
        """Get configured router"""
        self._setup_routes()
        return self.router
