import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from infrastructure.adapters.mongodb_database_adapter import MongoDatabaseAdapter
from domain.ports.database_port import EventRecord, ConsumerOffset


class TestMongoDatabaseAdapter:
    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        db = MagicMock()
        events_collection = MagicMock()
        offsets_collection = MagicMock()
        
        def get_item(key):
            if key == "kafka_events":
                return events_collection
            elif key == "consumer_offsets":
                return offsets_collection
            return MagicMock()
        
        db.__getitem__ = MagicMock(side_effect=get_item)
        client.__getitem__ = MagicMock(return_value=db)
        return client

    @pytest.fixture
    def adapter(self, mock_client):
        with patch('infrastructure.adapters.mongodb_database_adapter.MongoClient', return_value=mock_client):
            adapter = MongoDatabaseAdapter(uri="mongodb://localhost:27017/", database_name="test_db")
            adapter._client = mock_client
            adapter._db = mock_client.__getitem__.return_value
            adapter._events_collection = mock_client.__getitem__.return_value.__getitem__.return_value
            adapter._offsets_collection = mock_client.__getitem__.return_value.__getitem__.return_value
            return adapter

    def test_initialization(self, mock_client):
        with patch('infrastructure.adapters.mongodb_database_adapter.MongoClient', return_value=mock_client):
            adapter = MongoDatabaseAdapter(uri="mongodb://localhost:27017/")
            assert adapter._client is not None

    def test_save_event(self, adapter, mock_client):
        event = EventRecord(
            topic="test-topic",
            partition=0,
            offset=1,
            key="test-key",
            value='{"data": "test"}',
            timestamp=datetime.now()
        )
        mock_client.__getitem__.return_value.__getitem__.return_value.insert_one.return_value.inserted_id = "event-id"
        event_id = adapter.save_event(event)
        assert event_id is not None

    def test_get_event(self, adapter, mock_client):
        mock_collection = mock_client.__getitem__.return_value.__getitem__.return_value
        mock_collection.find_one.return_value = {
            "topic": "test-topic",
            "partition": 0,
            "offset": 1,
            "key": "test-key",
            "value": "test-value",
            "timestamp": datetime.now(),
            "headers": None,
            "processed": False,
            "error": None,
            "created_at": datetime.now()
        }
        event = adapter.get_event("event-id-123")
        assert event is not None

    def test_get_events_by_topic(self, adapter, mock_client):
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = MagicMock(return_value=iter([]))
        adapter._events_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = mock_cursor
        events = adapter.get_events_by_topic("test-topic")
        assert events == []

    def test_save_offset(self, adapter, mock_client):
        offset = ConsumerOffset(
            consumer_group="test-group",
            topic="test-topic",
            partition=0,
            offset=100
        )
        adapter._offsets_collection.update_one.return_value.acknowledged = True
        result = adapter.save_consumer_offset(offset)
        assert result is True

    def test_get_offset(self, adapter, mock_client):
        mock_collection = mock_client.__getitem__.return_value.__getitem__.return_value
        mock_collection.find_one.return_value = {
            "consumer_group": "test-group",
            "topic": "test-topic",
            "partition": 0,
            "offset": 100,
            "updated_at": datetime.now()
        }
        offset = adapter.get_consumer_offset("test-group", "test-topic", 0)
        assert offset is not None

    def test_close(self, adapter, mock_client):
        adapter.close()
        mock_client.close.assert_called_once()
