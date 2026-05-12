"""Integration tests for PostgreSQL adapter."""

import pytest
import os
from unittest.mock import patch

from kafka_messaging_internal.infra.adapters.postgresql.postgres_adapter import PostgresAdapter
from kafka_messaging_internal.shared.ports.database_port import EventRecord, ConsumerOffset
from kafka_messaging_internal.shared.errors.exceptions import DatabaseError


@pytest.mark.integration
class TestPostgresAdapter:
    """Integration tests for PostgreSQL adapter."""
    
    @pytest.fixture
    def test_config(self):
        """Test configuration for PostgreSQL."""
        return {
            'POSTGRES_DSN': os.getenv('TEST_DATABASE_URL', 'postgresql://test:test@localhost:5432/kafka_events_test'),
            'POSTGRES_MIN_CONNECTIONS': '1',
            'POSTGRES_MAX_CONNECTIONS': '2'
        }
    
    @pytest.fixture
    def adapter(self, test_config):
        """PostgreSQL adapter fixture."""
        adapter = PostgresAdapter(test_config)
        yield adapter
        adapter.close()
    
    def test_adapter_initialization_success(self, test_config):
        """Test successful adapter initialization."""
        adapter = PostgresAdapter(test_config)
        assert adapter is not None
        assert adapter.dsn == test_config['POSTGRES_DSN']
        adapter.close()
    
    def test_adapter_initialization_failure(self):
        """Test adapter initialization with invalid DSN."""
        invalid_config = {
            'POSTGRES_DSN': 'postgresql://invalid:invalid@invalid:5432/invalid',
            'POSTGRES_MIN_CONNECTIONS': '1',
            'POSTGRES_MAX_CONNECTIONS': '2'
        }
        
        with pytest.raises(DatabaseError) as exc_info:
            PostgresAdapter(invalid_config)
        
        assert exc_info.value.code == "DB_CONNECTION_FAILED"
    
    def test_save_event_success(self, adapter):
        """Test successful event saving."""
        import datetime
        event = EventRecord(
            event_id="test-event-123",
            topic="test-topic",
            partition=0,
            offset=123,
            key="test-key",
            value={"message": "test data"},
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            headers={"source": "test"}
        )
        
        event_id = adapter.save_event(event)
        assert event_id is not None
        assert isinstance(event_id, str)
    
    def test_save_event_duplicate(self, adapter):
        """Test saving duplicate event."""
        import datetime
        event = EventRecord(
            event_id="test-event-duplicate",
            topic="test-topic",
            partition=0,
            offset=456,
            key="test-key",
            value={"message": "test data"},
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        
        # Save first time
        event_id_1 = adapter.save_event(event)
        assert event_id_1 is not None
        
        # Save second time (should update)
        event_id_2 = adapter.save_event(event)
        assert event_id_2 == event_id_1
    
    def test_save_events_batch_success(self, adapter):
        """Test successful batch event saving."""
        import datetime
        events = [
            EventRecord(
                event_id=f"test-batch-{i}",
                topic="test-batch-topic",
                partition=0,
                offset=i,
                key=f"key-{i}",
                value={"message": f"test data {i}"},
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            for i in range(3)
        ]
        
        event_ids = adapter.save_events_batch(events)
        assert len(event_ids) == 3
        assert all(event_id is not None for event_id in event_ids)
    
    def test_get_event_success(self, adapter):
        """Test successful event retrieval."""
        import datetime
        event = EventRecord(
            event_id="test-get-event",
            topic="test-get-topic",
            partition=0,
            offset=789,
            key="test-key",
            value={"message": "test data"},
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        
        # Save event first
        saved_event_id = adapter.save_event(event)
        
        # Retrieve event
        retrieved_event = adapter.get_event(saved_event_id)
        
        assert retrieved_event is not None
        assert retrieved_event.event_id == saved_event_id
        assert retrieved_event.topic == "test-get-topic"
        assert retrieved_event.partition == 0
        assert retrieved_event.offset == 789
        assert retrieved_event.key == "test-key"
        assert retrieved_event.value == {"message": "test data"}
    
    def test_get_event_not_found(self, adapter):
        """Test event retrieval when not found."""
        event = adapter.get_event("non-existent-event-id")
        assert event is None
    
    def test_get_events_by_topic_success(self, adapter):
        """Test successful events retrieval by topic."""
        import datetime
        
        # Save multiple events for the same topic
        events = []
        for i in range(5):
            event = EventRecord(
                event_id=f"test-topic-query-{i}",
                topic="test-query-topic",
                partition=0,
                offset=i,
                key=f"key-{i}",
                value={"message": f"test data {i}"},
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            adapter.save_event(event)
            events.append(event)
        
        # Retrieve events by topic
        retrieved_events = adapter.get_events_by_topic("test-query-topic", limit=3)
        
        assert len(retrieved_events) == 3
        for event in retrieved_events:
            assert event.topic == "test-query-topic"
    
    def test_mark_event_processed_success(self, adapter):
        """Test successful event processing mark."""
        import datetime
        event = EventRecord(
            event_id="test-mark-processed",
            topic="test-mark-topic",
            partition=0,
            offset=999,
            key="test-key",
            value={"message": "test data"},
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        
        # Save event first
        saved_event_id = adapter.save_event(event)
        
        # Mark as processed
        success = adapter.mark_event_processed(saved_event_id)
        assert success is True
        
        # Verify it's marked as processed
        retrieved_event = adapter.get_event(saved_event_id)
        assert retrieved_event.processed is True
    
    def test_save_consumer_offset_success(self, adapter):
        """Test successful consumer offset saving."""
        import datetime
        offset = ConsumerOffset(
            consumer_group="test-group",
            topic="test-offset-topic",
            partition=0,
            offset=1234,
            updated_at=datetime.datetime.now(datetime.timezone.utc)
        )
        
        success = adapter.save_consumer_offset(offset)
        assert success is True
    
    def test_get_consumer_offset_success(self, adapter):
        """Test successful consumer offset retrieval."""
        import datetime
        offset = ConsumerOffset(
            consumer_group="test-get-group",
            topic="test-get-offset-topic",
            partition=0,
            offset=5678,
            updated_at=datetime.datetime.now(datetime.timezone.utc)
        )
        
        # Save offset first
        adapter.save_consumer_offset(offset)
        
        # Retrieve offset
        retrieved_offset = adapter.get_consumer_offset("test-get-group", "test-get-offset-topic", 0)
        
        assert retrieved_offset is not None
        assert retrieved_offset.consumer_group == "test-get-group"
        assert retrieved_offset.topic == "test-get-offset-topic"
        assert retrieved_offset.partition == 0
        assert retrieved_offset.offset == 5678
    
    def test_get_consumer_offset_not_found(self, adapter):
        """Test consumer offset retrieval when not found."""
        offset = adapter.get_consumer_offset("non-existent-group", "non-existent-topic", 0)
        assert offset is None
    
    def test_get_event_count_success(self, adapter):
        """Test successful event count retrieval."""
        import datetime
        
        # Save some events
        for i in range(3):
            event = EventRecord(
                event_id=f"test-count-{i}",
                topic="test-count-topic",
                partition=0,
                offset=i,
                key=f"key-{i}",
                value={"message": f"test data {i}"},
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            adapter.save_event(event)
        
        # Get count for specific topic
        count = adapter.get_event_count("test-count-topic")
        assert count >= 3
        
        # Get total count
        total_count = adapter.get_event_count()
        assert total_count >= 3
    
    def test_delete_events_by_topic_success(self, adapter):
        """Test successful events deletion by topic."""
        import datetime
        
        # Save events for deletion
        for i in range(2):
            event = EventRecord(
                event_id=f"test-delete-{i}",
                topic="test-delete-topic",
                partition=0,
                offset=i,
                key=f"key-{i}",
                value={"message": f"test data {i}"},
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            adapter.save_event(event)
        
        # Delete events
        deleted_count = adapter.delete_events_by_topic("test-delete-topic")
        assert deleted_count >= 2
        
        # Verify events are deleted
        remaining_events = adapter.get_events_by_topic("test-delete-topic")
        assert len(remaining_events) == 0
