import pytest
from unittest.mock import Mock
from fastapi import HTTPException

from application.api.v1.consumer_api import (
    ConsumerAPI,
    ConsumeMessageRequest,
    ConsumerOffsetRequest
)
from application.api.v1.validators import ValidationError
from domain.ports.consumer_port import ConsumeParams, ConsumerOffsetParams


@pytest.fixture
def mock_consumer():
    consumer = Mock()
    consumer.consume.return_value = [
        {
            "topic": "test-topic",
            "partition": 0,
            "offset": 100,
            "key": "test-key",
            "value": "test-value",
            "timestamp": 1234567890,
            "headers": {}
        }
    ]
    consumer.commit_offset.return_value = True
    consumer.get_offset.return_value = 100
    consumer.subscribe.return_value = True
    consumer.unsubscribe.return_value = True
    consumer.list_subscriptions.return_value = ["topic1", "topic2"]
    return consumer


@pytest.fixture
def consumer_api(mock_consumer):
    return ConsumerAPI(mock_consumer)


class TestConsumeMessageRequest:
    def test_valid_request(self):
        request = ConsumeMessageRequest(
            topic="test-topic",
            consumer_group="test-group",
            max_messages=10
        )
        assert request.topic == "test-topic"
        assert request.consumer_group == "test-group"


class TestConsumerAPIConsumeMessages:
    def test_consume_messages_success(self, consumer_api, mock_consumer):
        request = ConsumeMessageRequest(
            topic="test-topic",
            consumer_group="test-group",
            max_messages=10
        )
        
        response = consumer_api._consume_messages(request)
        
        assert response.success is True
        assert response.count == 1
        mock_consumer.consume.assert_called_once()

    def test_consume_messages_empty_topic_raises_400(self, consumer_api):
        request = ConsumeMessageRequest(
            topic="",
            consumer_group="test-group",
            max_messages=10
        )
        
        with pytest.raises(HTTPException) as exc:
            consumer_api._consume_messages(request)
        
        assert exc.value.status_code == 400
        assert "topic" in str(exc.value.detail)

    def test_consume_messages_empty_group_raises_400(self, consumer_api):
        request = ConsumeMessageRequest(
            topic="test-topic",
            consumer_group="",
            max_messages=10
        )
        
        with pytest.raises(HTTPException) as exc:
            consumer_api._consume_messages(request)
        
        assert exc.value.status_code == 400
        assert "consumer_group" in str(exc.value.detail)

    def test_consume_messages_invalid_max_raises_400(self, consumer_api):
        request = ConsumeMessageRequest(
            topic="test-topic",
            consumer_group="test-group",
            max_messages=0
        )
        
        with pytest.raises(HTTPException) as exc:
            consumer_api._consume_messages(request)
        
        assert exc.value.status_code == 400
        assert "max_messages" in str(exc.value.detail)


class TestConsumerAPICommitOffset:
    def test_commit_offset_success(self, consumer_api, mock_consumer):
        request = ConsumerOffsetRequest(
            consumer_group="test-group",
            topic="test-topic",
            partition=0,
            offset=100
        )

        response = consumer_api._commit_offset(request)

        assert response["success"] is True
        mock_consumer.commit_offset.assert_called_once()

    def test_commit_offset_empty_group_raises_400(self, consumer_api):
        request = ConsumerOffsetRequest(
            consumer_group="",
            topic="test-topic",
            partition=0,
            offset=100
        )

        with pytest.raises(HTTPException) as exc:
            consumer_api._commit_offset(request)

        assert exc.value.status_code == 400
        assert "consumer_group" in str(exc.value.detail)

    def test_commit_offset_negative_offset_raises_400(self, consumer_api):
        request = ConsumerOffsetRequest(
            consumer_group="test-group",
            topic="test-topic",
            partition=0,
            offset=-1
        )

        with pytest.raises(HTTPException) as exc:
            consumer_api._commit_offset(request)

        assert exc.value.status_code == 400
        assert "offset" in str(exc.value.detail)


class TestConsumerAPIGetOffset:
    def test_get_offset_success(self, consumer_api, mock_consumer):
        response = consumer_api._get_offset("test-group", "test-topic", 0)
        
        assert response["consumer_group"] == "test-group"
        assert response["offset"] == 100

    def test_get_offset_empty_group_raises_400(self, consumer_api):
        with pytest.raises(HTTPException) as exc:
            consumer_api._get_offset("", "test-topic", 0)
        
        assert exc.value.status_code == 400
        assert "consumer_group" in str(exc.value.detail)


class TestConsumerAPISubscribe:
    def test_subscribe_success(self, consumer_api, mock_consumer):
        response = consumer_api._subscribe("test-topic", "test-group")
        
        assert response["success"] is True
        assert response["topic"] == "test-topic"

    def test_subscribe_empty_topic_raises_400(self, consumer_api):
        with pytest.raises(HTTPException) as exc:
            consumer_api._subscribe("", "test-group")
        
        assert exc.value.status_code == 400
        assert "topic" in str(exc.value.detail)


class TestConsumerAPIUnsubscribe:
    def test_unsubscribe_success(self, consumer_api, mock_consumer):
        response = consumer_api._unsubscribe("test-topic", "test-group")
        
        assert response["success"] is True

    def test_unsubscribe_empty_group_raises_400(self, consumer_api):
        with pytest.raises(HTTPException) as exc:
            consumer_api._unsubscribe("test-topic", "")
        
        assert exc.value.status_code == 400
        assert "consumer_group" in str(exc.value.detail)


class TestConsumerAPIListSubscriptions:
    def test_list_subscriptions_success(self, consumer_api, mock_consumer):
        response = consumer_api._list_subscriptions("test-group")
        
        assert "subscriptions" in response
        assert len(response["subscriptions"]) == 2

    def test_list_subscriptions_empty_group_raises_400(self, consumer_api):
        with pytest.raises(HTTPException) as exc:
            consumer_api._list_subscriptions("")
        
        assert exc.value.status_code == 400
        assert "consumer_group" in str(exc.value.detail)
