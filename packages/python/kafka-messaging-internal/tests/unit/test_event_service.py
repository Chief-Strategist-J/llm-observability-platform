"""Unit tests for EventService."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from kafka_messaging_internal.features.events.service import EventService
from kafka_messaging_internal.shared.ports.database_port import DatabasePort
from kafka_messaging_internal.shared.types.events import EventRecord


class TestEventService:
    """Test cases for EventService"""

    @pytest.fixture
    def mock_database(self):
        """Mock database port"""
        database = Mock(spec=DatabasePort)
        database.save_event = AsyncMock(return_value="test_event_id")
        database.save_events_batch = AsyncMock(return_value=["id1", "id2"])
        database.mark_event_processed = AsyncMock(return_value=True)
        database.save_consumer_offset = AsyncMock(return_value=True)
        database.get_consumer_offset = Mock(return_value=None)
        database.get_events_by_topic = Mock(return_value=[])
        database.get_event_count = Mock(return_value=0)
        database.delete_events_by_topic = Mock(return_value=5)
        database.get_unprocessed_events = Mock(return_value=[])
        database.close = Mock()
        return database

    @pytest.fixture
    def event_service(self, mock_database):
        """Create event service instance"""
        return EventService(mock_database)

    def test_init(self, event_service, mock_database):
        """Test service initialization"""
        assert event_service._database == mock_database

    @pytest.mark.asyncio
    async def test_process_kafka_record(self, event_service, mock_database):
        """Test processing a single Kafka record"""
        record = {
            'topic': 'test-topic',
            'partition': 0,
            'offset': 123,
            'key': 'test-key',
            'value': {'data': 'test'},
            'timestamp': 1640995200000  # milliseconds
        }
        
        event_id = await event_service.process_kafka_record(record)
        
        assert event_id == "test_event_id"
        mock_database.save_event.assert_called_once()
        
        # Verify the EventRecord was created correctly
        call_args = mock_database.save_event.call_args[0][0]
        assert isinstance(call_args, EventRecord)
        assert call_args.topic == 'test-topic'
        assert call_args.partition == 0
        assert call_args.offset == 123
        assert call_args.key == 'test-key'
        assert call_args.value == {'data': 'test'}

    @pytest.mark.asyncio
    async def test_process_kafka_records_batch(self, event_service, mock_database):
        """Test processing multiple Kafka records"""
        records = [
            {
                'topic': 'test-topic',
                'partition': 0,
                'offset': 123,
                'key': 'key1',
                'value': {'data': 'test1'},
                'timestamp': 1640995200000
            },
            {
                'topic': 'test-topic',
                'partition': 0,
                'offset': 124,
                'key': 'key2',
                'value': {'data': 'test2'},
                'timestamp': 1640995200000
            }
        ]
        
        event_ids = await event_service.process_kafka_records_batch(records)
        
        assert event_ids == ["id1", "id2"]
        mock_database.save_events_batch.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_with_custom_logic_success(self, event_service, mock_database):
        """Test processing with custom logic - success case"""
        record = {
            'topic': 'test-topic',
            'partition': 0,
            'offset': 123,
            'key': 'test-key',
            'value': {'data': 'test'},
            'timestamp': 1640995200000
        }
        
        def processor(value):
            return {"processed": value}
        
        result = await event_service.process_with_custom_logic(record, processor)
        
        assert result["success"] is True
        assert "result" in result
        assert result["event_id"] == "test_event_id"
        mock_database.mark_event_processed.assert_called_once_with("test_event_id")

    @pytest.mark.asyncio
    async def test_process_with_custom_logic_failure(self, event_service, mock_database):
        """Test processing with custom logic - failure case"""
        record = {
            'topic': 'test-topic',
            'partition': 0,
            'offset': 123,
            'key': 'test-key',
            'value': {'data': 'test'},
            'timestamp': 1640995200000
        }
        
        def processor(value):
            raise ValueError("Processing failed")
        
        result = await event_service.process_with_custom_logic(record, processor)
        
        assert result["success"] is False
        assert "error" in result
        assert result["event_id"] == "test_event_id"
        mock_database.mark_event_processed.assert_called_once_with("test_event_id", error="Processing failed")

    @pytest.mark.asyncio
    async def test_save_consumer_offset(self, event_service, mock_database):
        """Test saving consumer offset"""
        mock_database.save_consumer_offset.return_value = True
        
        result = await event_service.save_consumer_offset("test-group", "test-topic", 0, 456)
        
        assert result is True
        mock_database.save_consumer_offset.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_consumer_offset(self, event_service, mock_database):
        """Test getting consumer offset"""
        from kafka_messaging_internal.shared.types.events import ConsumerOffset
        mock_offset = ConsumerOffset("test-group", "test-topic", 0, 456)
        mock_database.get_consumer_offset.return_value = mock_offset
        
        result = await event_service.get_consumer_offset("test-group", "test-topic", 0)
        
        assert result == 456
        mock_database.get_consumer_offset.assert_called_once_with("test-group", "test-topic", 0)

    @pytest.mark.asyncio
    async def test_get_consumer_offset_not_found(self, event_service, mock_database):
        """Test getting consumer offset when not found"""
        mock_database.get_consumer_offset.return_value = None
        
        result = await event_service.get_consumer_offset("test-group", "test-topic", 0)
        
        assert result is None
        mock_database.get_consumer_offset.assert_called_once_with("test-group", "test-topic", 0)

    def test_close(self, event_service, mock_database):
        """Test closing the service"""
        event_service.close()
        mock_database.close.assert_called_once()
