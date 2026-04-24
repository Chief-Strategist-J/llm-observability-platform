import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from infrastructure.messaging.domain.services.event_handler import EventHandler, ConsumerRecord
from infrastructure.messaging.domain.ports.database_port import EventRecord, ConsumerOffset


class TestConsumerRecord:
    def test_consumer_record_creation(self):
        record = ConsumerRecord(
            topic="test-topic",
            partition=0,
            offset=1,
            key="test-key",
            value={"data": "test"},
            timestamp=1234567890
        )
        assert record.topic == "test-topic"
        assert record.partition == 0
        assert record.offset == 1
        assert record.key == "test-key"
        assert record.value == {"data": "test"}
        assert record.timestamp == 1234567890

    def test_consumer_record_optional_headers(self):
        record = ConsumerRecord(
            topic="test-topic",
            partition=0,
            offset=1,
            key="test-key",
            value={"data": "test"},
            timestamp=1234567890,
            headers={"header1": "value1"}
        )
        assert record.headers == {"header1": "value1"}


class TestEventHandler:
    @pytest.fixture
    def mock_database(self):
        db = Mock()
        db.save_event.return_value = "event-id-123"
        db.save_offset.return_value = True
        return db

    @pytest.fixture
    def handler(self, mock_database):
        return EventHandler(database=mock_database)

    @pytest.fixture
    def sample_record(self):
        return ConsumerRecord(
            topic="test-topic",
            partition=0,
            offset=1,
            key="test-key",
            value={"data": "test"},
            timestamp=1234567890
        )

    def test_initialization(self, handler, mock_database):
        assert handler._database == mock_database

    def test_process_kafka_record(self, handler, sample_record, mock_database):
        event_id = handler.process_kafka_record(sample_record)
        assert event_id == "event-id-123"
        mock_database.save_event.assert_called_once()

    def test_process_kafka_record_with_none_key(self, handler, mock_database):
        record = ConsumerRecord(
            topic="test-topic",
            partition=0,
            offset=1,
            key=None,
            value={"data": "test"},
            timestamp=1234567890
        )
        handler.process_kafka_record(record)
        mock_database.save_event.assert_called_once()

    def test_process_kafka_records_batch(self, handler, sample_record, mock_database):
        records = [sample_record, sample_record]
        mock_database.save_events_batch.return_value = ["id1", "id2"]
        event_ids = handler.process_kafka_records_batch(records)
        assert len(event_ids) == 2
        mock_database.save_events_batch.assert_called_once()

    def test_save_consumer_offset(self, handler, mock_database):
        mock_database.save_consumer_offset.return_value = True
        result = handler.save_consumer_offset("test-group", "test-topic", 0, 100)
        assert result is True
        mock_database.save_consumer_offset.assert_called_once()

    def test_get_consumer_offset(self, handler, mock_database):
        mock_database.get_consumer_offset.return_value = ConsumerOffset(
            consumer_group="test-group",
            topic="test-topic",
            partition=0,
            offset=100
        )
        offset = handler.get_consumer_offset("test-group", "test-topic", 0)
        assert offset == 100
        mock_database.get_consumer_offset.assert_called_once()

    def test_get_events_by_topic(self, handler, mock_database):
        mock_database.get_events_by_topic.return_value = []
        events = handler.get_events_by_topic("test-topic")
        assert events == []
        mock_database.get_events_by_topic.assert_called_once()

    def test_get_event_count(self, handler, mock_database):
        mock_database.get_event_count.return_value = 10
        count = handler.get_event_count("test-topic")
        assert count == 10
        mock_database.get_event_count.assert_called_once()

    def test_close(self, handler, mock_database):
        handler.close()
        mock_database.close.assert_called_once()
