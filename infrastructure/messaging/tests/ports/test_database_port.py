import pytest
from dataclasses import dataclass
from datetime import datetime
from domain.ports.database_port import DatabasePort, EventRecord, ConsumerOffset


class TestEventRecord:
    def test_event_record_creation(self):
        record = EventRecord(
            topic="test-topic",
            partition=0,
            offset=1,
            key="test-key",
            value='{"data": "test"}',
            timestamp=datetime.now()
        )
        assert record.topic == "test-topic"
        assert record.partition == 0
        assert record.offset == 1
        assert record.key == "test-key"

    def test_event_record_optional_fields(self):
        record = EventRecord(
            topic="test-topic",
            partition=0,
            offset=1,
            key=None,
            value='{"data": "test"}',
            timestamp=datetime.now()
        )
        assert record.key is None


class TestConsumerOffset:
    def test_consumer_offset_creation(self):
        offset = ConsumerOffset(
            consumer_group="test-group",
            topic="test-topic",
            partition=0,
            offset=100
        )
        assert offset.consumer_group == "test-group"
        assert offset.topic == "test-topic"
        assert offset.partition == 0
        assert offset.offset == 100


class TestDatabasePort:
    def test_port_is_abstract(self):
        with pytest.raises(TypeError):
            DatabasePort()


class MockDatabasePort(DatabasePort):
    def save_event(self, event: EventRecord) -> str:
        return "test-id"

    def save_events_batch(self, events: list) -> list:
        return ["test-id" for _ in events]

    def get_event(self, event_id: str) -> EventRecord:
        return EventRecord(
            topic="test",
            partition=0,
            offset=1,
            key="key",
            value="value",
            timestamp=datetime.now()
        )

    def get_events_by_topic(self, topic: str, limit: int = 100, offset: int = 0) -> list:
        return []

    def get_unprocessed_events(self, limit: int = 100) -> list:
        return []

    def mark_event_processed(self, event_id: str, error: str = None) -> bool:
        return True

    def save_consumer_offset(self, offset: ConsumerOffset) -> bool:
        return True

    def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> ConsumerOffset:
        return ConsumerOffset(
            consumer_group=consumer_group,
            topic=topic,
            partition=partition,
            offset=0
        )

    def delete_events_by_topic(self, topic: str) -> int:
        return 0

    def get_event_count(self, topic: str = None) -> int:
        return 0

    def close(self):
        pass


class TestMockDatabasePort:
    @pytest.fixture
    def mock_db(self):
        return MockDatabasePort()

    def test_save_event(self, mock_db):
        event = EventRecord(
            topic="test",
            partition=0,
            offset=1,
            key="key",
            value="value",
            timestamp=datetime.now()
        )
        result = mock_db.save_event(event)
        assert result == "test-id"

    def test_get_event(self, mock_db):
        event = mock_db.get_event("test-id")
        assert event.topic == "test"

    def test_get_events_by_topic(self, mock_db):
        events = mock_db.get_events_by_topic("test-topic")
        assert events == []

    def test_save_offset(self, mock_db):
        offset = ConsumerOffset(
            consumer_group="test-group",
            topic="test-topic",
            partition=0,
            offset=100
        )
        result = mock_db.save_consumer_offset(offset)
        assert result is True

    def test_get_offset(self, mock_db):
        offset = mock_db.get_consumer_offset("test-group", "test-topic", 0)
        assert offset.offset == 0

    def test_close(self, mock_db):
        mock_db.close()
