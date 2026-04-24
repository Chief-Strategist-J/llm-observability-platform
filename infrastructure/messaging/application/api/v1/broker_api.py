from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status, APIRouter
from pydantic import BaseModel, Field

from infrastructure.messaging.domain.ports.broker_port import BrokerPort
from infrastructure.messaging.application.api.v1.validators import Preconditions, Postconditions, ValidationError


class BrokerMetadataResponse(BaseModel):
    cluster_id: str
    controller_id: int
    broker_count: int
    topic_count: int


class BrokerInfoResponse(BaseModel):
    broker_id: int
    host: str
    port: int
    rack: Optional[str]


class TopicMetadataResponse(BaseModel):
    topic_name: str
    partition_count: int
    replication_factor: int
    partitions: List[Dict[str, Any]]


class ConsumerGroupResponse(BaseModel):
    group_id: str
    state: str
    members: int
    topics: List[str]


class ConsumerGroupLagResponse(BaseModel):
    group_id: str
    topic: str
    partition: int
    current_offset: int
    log_end_offset: int
    lag: int


class ClusterConfigResponse(BaseModel):
    config: Dict[str, str]


class BrokerAPI:
    def __init__(self, broker_port: BrokerPort):
        self._broker = broker_port
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        @self.router.get("/metadata", response_model=BrokerMetadataResponse)
        def get_broker_metadata_route():
            return self.get_broker_metadata()

        @self.router.get("/brokers", response_model=List[BrokerInfoResponse])
        def list_brokers_route():
            return self.list_brokers()

        @self.router.get("/brokers/{broker_id}", response_model=BrokerInfoResponse)
        def get_broker_info_route(broker_id: int):
            return self.get_broker_info(broker_id)

        @self.router.get("/topics")
        def list_topics_route():
            return self.list_topics()

        @self.router.get("/topics/{topic_name}/metadata", response_model=TopicMetadataResponse)
        def get_topic_metadata_route(topic_name: str):
            return self.get_topic_metadata(topic_name)

        @self.router.get("/consumer-groups", response_model=List[ConsumerGroupResponse])
        def get_consumer_groups_route():
            return self.get_consumer_groups()

        @self.router.get("/consumer-groups/{group_id}/lag", response_model=List[ConsumerGroupLagResponse])
        def get_consumer_group_lag_route(group_id: str):
            return self.get_consumer_group_lag(group_id)

        @self.router.get("/config", response_model=ClusterConfigResponse)
        def get_cluster_config_route():
            return self.get_cluster_config()

    def get_broker_metadata(self) -> BrokerMetadataResponse:
        try:
            metadata = self._broker.get_broker_metadata()
            Postconditions.validate_not_none(metadata, "get_broker_metadata")
            
            return BrokerMetadataResponse(
                cluster_id=metadata.get("cluster_id", ""),
                controller_id=metadata.get("controller_id", 0),
                broker_count=metadata.get("broker_count", 0),
                topic_count=metadata.get("topic_count", 0)
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get broker metadata: {str(e)}"
            )

    def list_brokers(self) -> List[BrokerInfoResponse]:
        try:
            brokers = self._broker.list_brokers()
            Postconditions.validate_not_none(brokers, "list_brokers")
            
            return [
                BrokerInfoResponse(
                    broker_id=broker.get("broker_id", 0),
                    host=broker.get("host", ""),
                    port=broker.get("port", 9092),
                    rack=broker.get("rack")
                )
                for broker in brokers
            ]
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list brokers: {str(e)}"
            )

    def get_broker_info(self, broker_id: int) -> BrokerInfoResponse:
        try:
            Preconditions.validate_positive(broker_id, "broker_id")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            broker_info = self._broker.get_broker_info(broker_id)
            Postconditions.validate_not_none(broker_info, "get_broker_info")
            
            return BrokerInfoResponse(
                broker_id=broker_info.get("broker_id", broker_id),
                host=broker_info.get("host", ""),
                port=broker_info.get("port", 9092),
                rack=broker_info.get("rack")
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get broker info: {str(e)}"
            )

    def list_topics(self) -> Dict[str, List[str]]:
        try:
            topics = self._broker.list_topics()
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

    def get_topic_metadata(self, topic_name: str) -> TopicMetadataResponse:
        try:
            Preconditions.validate_non_empty_string(topic_name, "topic_name")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            metadata = self._broker.get_topic_metadata(topic_name)
            Postconditions.validate_not_none(metadata, "get_topic_metadata")
            
            return TopicMetadataResponse(
                topic_name=metadata.get("topic_name", topic_name),
                partition_count=metadata.get("partition_count", 0),
                replication_factor=metadata.get("replication_factor", 1),
                partitions=metadata.get("partitions", [])
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get topic metadata: {str(e)}"
            )

    def get_consumer_groups(self) -> List[ConsumerGroupResponse]:
        try:
            groups = self._broker.get_consumer_groups()
            Postconditions.validate_not_none(groups, "get_consumer_groups")
            
            return [
                ConsumerGroupResponse(
                    group_id=group.get("group_id", ""),
                    state=group.get("state", ""),
                    members=group.get("members", 0),
                    topics=group.get("topics", [])
                )
                for group in groups
            ]
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get consumer groups: {str(e)}"
            )

    def get_consumer_group_lag(self, group_id: str) -> List[ConsumerGroupLagResponse]:
        try:
            Preconditions.validate_non_empty_string(group_id, "group_id")
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        try:
            lag_info = self._broker.get_consumer_group_lag(group_id)
            Postconditions.validate_not_none(lag_info, "get_consumer_group_lag")
            
            lag_list = lag_info if isinstance(lag_info, list) else [lag_info]
            
            return [
                ConsumerGroupLagResponse(
                    group_id=lag.get("group_id", group_id),
                    topic=lag.get("topic", ""),
                    partition=lag.get("partition", 0),
                    current_offset=lag.get("current_offset", 0),
                    log_end_offset=lag.get("log_end_offset", 0),
                    lag=lag.get("lag", 0)
                )
                for lag in lag_list
            ]
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get consumer group lag: {str(e)}"
            )

    def get_cluster_config(self) -> ClusterConfigResponse:
        try:
            config = self._broker.get_cluster_config()
            Postconditions.validate_not_none(config, "get_cluster_config")
            
            return ClusterConfigResponse(config=config)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get cluster config: {str(e)}"
            )
