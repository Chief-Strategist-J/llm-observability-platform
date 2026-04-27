import pytest
from unittest.mock import Mock
from fastapi import HTTPException
from datetime import datetime

from application.api.v1.database_api import (
    DatabaseAPI,
    EventRecordRequest,
    BatchEventRequest,
    ConsumerOffsetRequest,
    EventRecordResponse,
    BatchEventResponse,
    ConsumerOffsetResponse
)
from domain.ports.database_port import EventRecord, ConsumerOffset
from application.api.v1.validators import ValidationError


@pytest.fixture
def mock_database():
    return Mock()


@pytest.fixture
def database_api(mock_database):
    return DatabaseAPI(mock_database)


class TestEventRecordRequest:
    def test_valid_request(self):
        request = EventRecordRequest(
            topic="test-topic",
            partition=0,
            offset=1,
            key="test-key",
            value={"data": "test"},
            timestamp=datetime.now()
        )
        assert request.topic == "test-topic"
        assert request.partition == 0
        assert request.offset == 1






class TestBatchEventRequest:
    def test_valid_batch_request(self):
        events = [
            EventRecordRequest(topic="test-topic", partition=0, offset=i, value=f"value-{i}")
            for i in range(5)
        ]
        request = BatchEventRequest(events=events)
        assert len(request.events) == 5




class TestConsumerOffsetRequest:
    def test_valid_request(self):
        request = ConsumerOffsetRequest(
            consumer_group="test-group",
            topic="test-topic",
            partition=0,
            offset=100
        )
        assert request.consumer_group == "test-group"
        assert request.topic == "test-topic"




class TestDatabaseAPISaveEvent:
    def test_save_event_success(self, database_api, mock_database):
        request = EventRecordRequest(
            topic="test-topic",
            partition=0,
            offset=1,
            value="test-value"
        )
        mock_database.save_event.return_value = "event-id-123"
        
        response = database_api.save_event(request)
        
        assert response.event_id == "event-id-123"
        assert response.topic == "test-topic"
        mock_database.save_event.assert_called_once()

    def test_save_event_empty_topic_raises_400(self, database_api):
        request = EventRecordRequest(
            topic="",
            partition=0,
            offset=1,
            value="test"
        )
        
        with pytest.raises(HTTPException) as exc:
            database_api.save_event(request)
        
        assert exc.value.status_code == 400
        assert "topic" in str(exc.value.detail)

    def test_save_event_negative_partition_raises_400(self, database_api):
        request = EventRecordRequest(
            topic="test-topic",
            partition=-1,
            offset=1,
            value="test"
        )
        
        with pytest.raises(HTTPException) as exc:
            database_api.save_event(request)
        
        assert exc.value.status_code == 400
        assert "partition" in str(exc.value.detail)

    def test_save_event_database_error_raises_500(self, database_api, mock_database):
        request = EventRecordRequest(
            topic="test-topic",
            partition=0,
            offset=1,
            value="test"
        )
        mock_database.save_event.side_effect = Exception("Database error")
        
        with pytest.raises(HTTPException) as exc:
            database_api.save_event(request)
        
        assert exc.value.status_code == 500


class TestDatabaseAPISaveEventsBatch:
    def test_save_events_batch_success(self, database_api, mock_database):
        events = [
            EventRecordRequest(topic="test-topic", partition=0, offset=i, value=f"value-{i}")
            for i in range(3)
        ]
        request = BatchEventRequest(events=events)
        mock_database.save_events_batch.return_value = ["id-1", "id-2", "id-3"]
        
        response = database_api.save_events_batch(request)
        
        assert response.count == 3
        assert response.success is True
        mock_database.save_events_batch.assert_called_once()

    def test_save_events_batch_empty_list_raises_400(self, database_api):
        request = BatchEventRequest(events=[])
        
        with pytest.raises(HTTPException) as exc:
            database_api.save_events_batch(request)
        
        assert exc.value.status_code == 400
        assert "events" in str(exc.value.detail)




class TestDatabaseAPIGetEvent:
    def test_get_event_success(self, database_api, mock_database):
        event = EventRecord(
            topic="test-topic",
            partition=0,
            offset=1,
            key="key",
            value="value",
            timestamp=datetime.now()
        )
        mock_database.get_event.return_value = event
        
        response = database_api.get_event("event-id-123")
        
        assert response.topic == "test-topic"
        mock_database.get_event.assert_called_once_with("event-id-123")

    def test_get_event_not_found_raises_404(self, database_api, mock_database):
        mock_database.get_event.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            database_api.get_event("event-id-123")
        
        assert exc.value.status_code == 404

    def test_get_event_empty_id_raises_400(self, database_api):
        with pytest.raises(HTTPException) as exc:
            database_api.get_event("")
        
        assert exc.value.status_code == 400
        assert "event_id" in str(exc.value.detail)


class TestDatabaseAPIGetEventsByTopic:
    def test_get_events_by_topic_success(self, database_api, mock_database):
        events = [
            EventRecord(topic="test-topic", partition=0, offset=i, key=str(i), value=f"value-{i}", timestamp=datetime.now())
            for i in range(3)
        ]
        mock_database.get_events_by_topic.return_value = events
        
        response = database_api.get_events_by_topic("test-topic", limit=10, offset=0)
        
        assert len(response) == 3
        mock_database.get_events_by_topic.assert_called_once()

    def test_get_events_by_topic_empty_topic_raises_400(self, database_api):
        with pytest.raises(HTTPException) as exc:
            database_api.get_events_by_topic("", limit=10, offset=0)
        
        assert exc.value.status_code == 400
        assert "topic" in str(exc.value.detail)

    def test_get_events_by_topic_invalid_limit_raises_400(self, database_api):
        with pytest.raises(HTTPException) as exc:
            database_api.get_events_by_topic("test-topic", limit=0, offset=0)
        
        assert exc.value.status_code == 400
        assert "limit" in str(exc.value.detail)


class TestDatabaseAPIMarkEventProcessed:
    def test_mark_event_processed_success(self, database_api, mock_database):
        mock_database.mark_event_processed.return_value = True
        
        response = database_api.mark_event_processed("event-id-123")
        
        assert response["success"] is True
        mock_database.mark_event_processed.assert_called_once()

    def test_mark_event_processed_not_found_raises_404(self, database_api, mock_database):
        mock_database.mark_event_processed.return_value = False
        
        with pytest.raises(HTTPException) as exc:
            database_api.mark_event_processed("event-id-123")
        
        assert exc.value.status_code == 404

    def test_mark_event_processed_empty_id_raises_400(self, database_api):
        with pytest.raises(HTTPException) as exc:
            database_api.mark_event_processed("")
        
        assert exc.value.status_code == 400
        assert "event_id" in str(exc.value.detail)




class TestDatabaseAPISaveConsumerOffset:
    def test_save_consumer_offset_success(self, database_api, mock_database):
        request = ConsumerOffsetRequest(
            consumer_group="test-group",
            topic="test-topic",
            partition=0,
            offset=100
        )
        mock_database.save_consumer_offset.return_value = True
        
        response = database_api.save_consumer_offset(request)
        
        assert response["success"] is True
        mock_database.save_consumer_offset.assert_called_once()

    def test_save_consumer_offset_failure_raises_500(self, database_api, mock_database):
        request = ConsumerOffsetRequest(
            consumer_group="test-group",
            topic="test-topic",
            partition=0,
            offset=100
        )
        mock_database.save_consumer_offset.return_value = False
        
        with pytest.raises(HTTPException) as exc:
            database_api.save_consumer_offset(request)
        
        assert exc.value.status_code == 500

    def test_save_consumer_offset_empty_group_raises_400(self, database_api):
        request = ConsumerOffsetRequest(
            consumer_group="",
            topic="test-topic",
            partition=0,
            offset=100
        )
        
        with pytest.raises(HTTPException) as exc:
            database_api.save_consumer_offset(request)
        
        assert exc.value.status_code == 400
        assert "consumer_group" in str(exc.value.detail)


class TestDatabaseAPIGetConsumerOffset:
    def test_get_consumer_offset_success(self, database_api, mock_database):
        offset = ConsumerOffset(
            consumer_group="test-group",
            topic="test-topic",
            partition=0,
            offset=100
        )
        mock_database.get_consumer_offset.return_value = offset
        
        response = database_api.get_consumer_offset("test-group", "test-topic", 0)
        
        assert response.consumer_group == "test-group"
        assert response.offset == 100

    def test_get_consumer_offset_not_found_raises_404(self, database_api, mock_database):
        mock_database.get_consumer_offset.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            database_api.get_consumer_offset("test-group", "test-topic", 0)
        
        assert exc.value.status_code == 404

    def test_get_consumer_offset_empty_group_raises_400(self, database_api):
        with pytest.raises(HTTPException) as exc:
            database_api.get_consumer_offset("", "test-topic", 0)
        
        assert exc.value.status_code == 400
        assert "consumer_group" in str(exc.value.detail)



class TestDatabaseAPIDeleteEventsByTopic:
    def test_delete_events_by_topic_success(self, database_api, mock_database):
        mock_database.delete_events_by_topic.return_value = 5
        
        response = database_api.delete_events_by_topic("test-topic")
        
        assert response["deleted_count"] == 5
        mock_database.delete_events_by_topic.assert_called_once()

    def test_delete_events_by_topic_empty_topic_raises_400(self, database_api):
        with pytest.raises(HTTPException) as exc:
            database_api.delete_events_by_topic("")
        
        assert exc.value.status_code == 400
        assert "topic" in str(exc.value.detail)




class TestDatabaseAPIGetEventCount:
    def test_get_event_count_success(self, database_api, mock_database):
        mock_database.get_event_count.return_value = 100
        
        response = database_api.get_event_count("test-topic")
        
        assert response["count"] == 100

    def test_get_event_count_without_topic(self, database_api, mock_database):
        mock_database.get_event_count.return_value = 500
        
        response = database_api.get_event_count(None)
        
        assert response["count"] == 500
