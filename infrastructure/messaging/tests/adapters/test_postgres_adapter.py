import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from infrastructure.adapters.postgres_database_adapter import PostgresDatabaseAdapter
from domain.ports.database_port import EventRecord, ConsumerOffset


class TestPostgresDatabaseAdapter:
    @pytest.fixture
    def mock_pool(self):
        pool = MagicMock()
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        pool.getconn.return_value = conn
        pool.putconn.return_value = None
        return pool

    @pytest.fixture
    def adapter(self, mock_pool):
        with patch('infrastructure.adapters.postgres_database_adapter.psycopg2.pool.ThreadedConnectionPool', return_value=mock_pool):
            adapter = PostgresDatabaseAdapter(dsn="postgresql://test:test@localhost:5432/test")
            adapter._pool = mock_pool
            return adapter

    def test_initialization(self, mock_pool):
        with patch('infrastructure.adapters.postgres_database_adapter.psycopg2.pool.ThreadedConnectionPool', return_value=mock_pool):
            adapter = PostgresDatabaseAdapter(dsn="postgresql://test:test@localhost:5432/test")
            assert adapter._pool is not None

    def test_save_event(self, adapter, mock_pool):
        event = EventRecord(
            topic="test-topic",
            partition=0,
            offset=1,
            key="test-key",
            value='{"data": "test"}',
            timestamp=datetime.now()
        )
        event_id = adapter.save_event(event)
        assert event_id is not None

    def test_get_event(self, adapter, mock_pool):
        mock_pool.getconn.return_value.cursor.return_value.fetchone.return_value = (
            "test-topic", 0, 1, "key", "value", datetime.now(), None, False, None, datetime.now()
        )
        event = adapter.get_event("event-id-123")
        assert event is not None

    def test_get_events_by_topic(self, adapter, mock_pool):
        mock_pool.getconn.return_value.cursor.return_value.fetchall.return_value = []
        events = adapter.get_events_by_topic("test-topic")
        assert events == []

    def test_save_offset(self, adapter, mock_pool):
        offset = ConsumerOffset(
            consumer_group="test-group",
            topic="test-topic",
            partition=0,
            offset=100
        )
        result = adapter.save_consumer_offset(offset)
        assert result is True

    def test_get_offset(self, adapter, mock_pool):
        mock_cursor = mock_pool.getconn.return_value.cursor.return_value
        mock_cursor.fetchone.return_value = (
            "test-group", "test-topic", 0, 100, datetime.now()
        )
        offset = adapter.get_consumer_offset("test-group", "test-topic", 0)
        assert offset is not None

    def test_close(self, adapter, mock_pool):
        adapter.close()
        mock_pool.closeall.assert_called_once()
