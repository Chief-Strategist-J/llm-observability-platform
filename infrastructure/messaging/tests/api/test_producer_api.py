import pytest
from unittest.mock import Mock
from fastapi import HTTPException

from infrastructure.messaging.application.api.v1.producer_api import (
    ProducerAPI,
    ProduceMessageRequest,
    BatchProduceMessageRequest
)
from infrastructure.messaging.application.api.v1.validators import ValidationError


@pytest.fixture
def mock_producer():
    producer = Mock()
    producer.produce.return_value = {
        "topic": "test-topic",
        "partition": 0,
        "offset": 100,
        "timestamp": 1234567890
    }
    producer.list_topics.return_value = ["topic1", "topic2"]
    producer.create_topic.return_value = True
    return producer


@pytest.fixture
def producer_api(mock_producer):
    return ProducerAPI(mock_producer)


class TestProduceMessageRequest:
    def test_valid_request(self):
        request = ProduceMessageRequest(
            topic="test-topic",
            key="test-key",
            value="test-value",
            partition=0
        )
        assert request.topic == "test-topic"
        assert request.key == "test-key"


class TestProducerAPIProduceMessage:
    def test_produce_message_success(self, producer_api, mock_producer):
        request = ProduceMessageRequest(
            topic="test-topic",
            key="test-key",
            value="test-value"
        )
        
        response = producer_api._produce_message(request)
        
        assert response.success is True
        assert response.topic == "test-topic"
        mock_producer.produce.assert_called_once()

    def test_produce_message_empty_topic_raises_400(self, producer_api):
        request = ProduceMessageRequest(
            topic="",
            key="test-key",
            value="test-value"
        )
        
        with pytest.raises(HTTPException) as exc:
            producer_api._produce_message(request)
        
        assert exc.value.status_code == 400
        assert "topic" in str(exc.value.detail)

    def test_produce_message_negative_partition_raises_400(self, producer_api):
        request = ProduceMessageRequest(
            topic="test-topic",
            partition=-1,
            value="test-value"
        )
        
        with pytest.raises(HTTPException) as exc:
            producer_api._produce_message(request)
        
        assert exc.value.status_code == 400
        assert "partition" in str(exc.value.detail)


class TestProducerAPIProduceMessagesBatch:
    def test_produce_messages_batch_success(self, producer_api, mock_producer):
        messages = [
            ProduceMessageRequest(topic="test-topic", value=f"value-{i}")
            for i in range(3)
        ]
        request = BatchProduceMessageRequest(messages=messages)
        
        response = producer_api._produce_messages_batch(request)
        
        assert response.count == 3
        assert response.success is True

    def test_produce_messages_batch_empty_list_raises_400(self, producer_api):
        request = BatchProduceMessageRequest(messages=[])
        
        with pytest.raises(HTTPException) as exc:
            producer_api._produce_messages_batch(request)
        
        assert exc.value.status_code == 400
        assert "messages" in str(exc.value.detail)


class TestProducerAPIListTopics:
    def test_list_topics_success(self, producer_api, mock_producer):
        response = producer_api._list_topics()
        
        assert "topics" in response
        assert len(response["topics"]) == 2


class TestProducerAPICreateTopic:
    def test_create_topic_success(self, producer_api, mock_producer):
        response = producer_api._create_topic("new-topic", 3, 2)
        
        assert response["success"] is True
        assert response["topic"] == "new-topic"

    def test_create_topic_empty_name_raises_400(self, producer_api):
        with pytest.raises(HTTPException) as exc:
            producer_api._create_topic("", 3, 2)
        
        assert exc.value.status_code == 400
        assert "topic_name" in str(exc.value.detail)

    def test_create_topic_invalid_partitions_raises_400(self, producer_api):
        with pytest.raises(HTTPException) as exc:
            producer_api._create_topic("test-topic", 0, 2)
        
        assert exc.value.status_code == 400
        assert "partitions" in str(exc.value.detail)
