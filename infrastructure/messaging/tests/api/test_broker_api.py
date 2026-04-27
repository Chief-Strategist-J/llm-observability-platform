import pytest
from unittest.mock import Mock
from fastapi import HTTPException

from application.api.v1.broker_api import (
    BrokerAPI,
    BrokerMetadataResponse,
    BrokerInfoResponse,
    TopicMetadataResponse,
    ConsumerGroupResponse,
    ConsumerGroupLagResponse,
    ClusterConfigResponse
)
from application.api.v1.validators import ValidationError


@pytest.fixture
def mock_broker():
    broker = Mock()
    broker.get_broker_metadata.return_value = {
        "cluster_id": "test-cluster",
        "controller_id": 1,
        "broker_count": 3,
        "topic_count": 10
    }
    broker.list_brokers.return_value = [
        {
            "broker_id": 1,
            "host": "localhost",
            "port": 9092,
            "rack": "rack1"
        },
        {
            "broker_id": 2,
            "host": "localhost",
            "port": 9093,
            "rack": "rack2"
        }
    ]
    broker.get_broker_info.return_value = {
        "broker_id": 1,
        "host": "localhost",
        "port": 9092,
        "rack": "rack1"
    }
    broker.list_topics.return_value = ["topic1", "topic2", "topic3"]
    broker.get_topic_metadata.return_value = {
        "topic_name": "test-topic",
        "partition_count": 3,
        "replication_factor": 2,
        "partitions": [
            {"partition": 0, "leader": 1, "replicas": [1, 2]},
            {"partition": 1, "leader": 2, "replicas": [2, 1]},
            {"partition": 2, "leader": 1, "replicas": [1, 2]}
        ]
    }
    broker.get_consumer_groups.return_value = [
        {
            "group_id": "group1",
            "state": "Stable",
            "members": 3,
            "topics": ["topic1", "topic2"]
        },
        {
            "group_id": "group2",
            "state": "Stable",
            "members": 1,
            "topics": ["topic3"]
        }
    ]
    broker.get_consumer_group_lag.return_value = [
        {
            "group_id": "group1",
            "topic": "topic1",
            "partition": 0,
            "current_offset": 100,
            "log_end_offset": 150,
            "lag": 50
        }
    ]
    broker.get_cluster_config.return_value = {
        "num.partitions": "3",
        "default.replication.factor": "2"
    }
    return broker


@pytest.fixture
def broker_api(mock_broker):
    return BrokerAPI(mock_broker)


class TestBrokerAPIGetBrokerMetadata:
    def test_get_broker_metadata_success(self, broker_api, mock_broker):
        response = broker_api.get_broker_metadata()
        
        assert response.cluster_id == "test-cluster"
        assert response.broker_count == 3
        assert response.topic_count == 10
        mock_broker.get_broker_metadata.assert_called_once()


class TestBrokerAPIListBrokers:
    def test_list_brokers_success(self, broker_api, mock_broker):
        response = broker_api.list_brokers()
        
        assert len(response) == 2
        assert response[0].broker_id == 1
        assert response[0].host == "localhost"
        mock_broker.list_brokers.assert_called_once()


class TestBrokerAPIGetBrokerInfo:
    def test_get_broker_info_success(self, broker_api, mock_broker):
        response = broker_api.get_broker_info(1)
        
        assert response.broker_id == 1
        assert response.host == "localhost"
        assert response.port == 9092
        mock_broker.get_broker_info.assert_called_once_with(1)

    def test_get_broker_info_invalid_id_raises_400(self, broker_api):
        with pytest.raises(HTTPException) as exc:
            broker_api.get_broker_info(0)
        
        assert exc.value.status_code == 400
        assert "broker_id" in str(exc.value.detail)

    def test_get_broker_info_negative_id_raises_400(self, broker_api):
        with pytest.raises(HTTPException) as exc:
            broker_api.get_broker_info(-1)
        
        assert exc.value.status_code == 400
        assert "broker_id" in str(exc.value.detail)


class TestBrokerAPIListTopics:
    def test_list_topics_success(self, broker_api, mock_broker):
        response = broker_api.list_topics()
        
        assert "topics" in response
        assert len(response["topics"]) == 3
        assert "topic1" in response["topics"]
        mock_broker.list_topics.assert_called_once()


class TestBrokerAPIGetTopicMetadata:
    def test_get_topic_metadata_success(self, broker_api, mock_broker):
        response = broker_api.get_topic_metadata("test-topic")
        
        assert response.topic_name == "test-topic"
        assert response.partition_count == 3
        assert response.replication_factor == 2
        assert len(response.partitions) == 3
        mock_broker.get_topic_metadata.assert_called_once_with("test-topic")

    def test_get_topic_metadata_empty_name_raises_400(self, broker_api):
        with pytest.raises(HTTPException) as exc:
            broker_api.get_topic_metadata("")
        
        assert exc.value.status_code == 400
        assert "topic_name" in str(exc.value.detail)


class TestBrokerAPIGetConsumerGroups:
    def test_get_consumer_groups_success(self, broker_api, mock_broker):
        response = broker_api.get_consumer_groups()
        
        assert len(response) == 2
        assert response[0].group_id == "group1"
        assert response[0].members == 3
        mock_broker.get_consumer_groups.assert_called_once()


class TestBrokerAPIGetConsumerGroupLag:
    def test_get_consumer_group_lag_success(self, broker_api, mock_broker):
        response = broker_api.get_consumer_group_lag("group1")
        
        assert len(response) == 1
        assert response[0].group_id == "group1"
        assert response[0].lag == 50
        mock_broker.get_consumer_group_lag.assert_called_once_with("group1")

    def test_get_consumer_group_lag_empty_group_raises_400(self, broker_api):
        with pytest.raises(HTTPException) as exc:
            broker_api.get_consumer_group_lag("")
        
        assert exc.value.status_code == 400
        assert "group_id" in str(exc.value.detail)


class TestBrokerAPIGetClusterConfig:
    def test_get_cluster_config_success(self, broker_api, mock_broker):
        response = broker_api.get_cluster_config()
        
        assert "num.partitions" in response.config
        assert "default.replication.factor" in response.config
        mock_broker.get_cluster_config.assert_called_once()
