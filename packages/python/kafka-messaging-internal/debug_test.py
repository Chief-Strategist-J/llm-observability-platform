import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone
import sys
from kafka_messaging_internal.features.event_processing.service import EventProcessingService

@pytest.mark.asyncio
async def test_query_events_success(mock_database_port):
    service = EventProcessingService(mock_database_port)

    mock_event = Mock()
    mock_event.event_id = "test-id"
    mock_event.topic = "test-topic"
    mock_event.partition = 0
    mock_event.offset = 123
    mock_event.key = "test-key"
    mock_event.value = {"data": "test"}
    mock_event.timestamp = datetime.now(timezone.utc)
    mock_event.headers = {}
    mock_event.processed = False
    mock_event.error = None
    mock_event.created_at = datetime.now(timezone.utc)

    print("Before:", mock_database_port.get_events_by_topic.return_value)
    mock_database_port.get_events_by_topic.return_value = [mock_event]
    print("After:", mock_database_port.get_events_by_topic.return_value)

    events = await service.query_events({"topic": "test-topic", "limit": 10, "offset": 0})
    print("Events received:", events)

    assert isinstance(events, list)
    assert len(events) == 1
    mock_database_port.get_events_by_topic.assert_called_once_with("test-topic", 10, 0)
