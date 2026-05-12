"""Unit tests for event processing feature."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from kafka_messaging_internal.features.event_processing.service import EventProcessingService
from kafka_messaging_internal.shared.errors.exceptions import ValidationError, BusinessError


class TestEventProcessingService:
    """Unit tests for EventProcessingService."""
    
    def test_process_event_success(self, mock_database_port, sample_event_data):
        """Test successful event processing."""
        service = EventProcessingService(mock_database_port)
        
        # Mock database calls
        mock_database_port.get_event.return_value = None
        mock_database_port.save_event.return_value = "test-event-id"
        
        result = service.process_event(sample_event_data)
        
        assert result["success"] is True
        assert result["event_id"] == "test-event-id"
        assert result["error"] is None
        mock_database_port.save_event.assert_called_once()
        mock_database_port.mark_event_processed.assert_called_once_with("test-event-id")
    
    def test_process_event_validation_error(self, mock_database_port):
        """Test event processing with invalid data."""
        service = EventProcessingService(mock_database_port)
        
        invalid_data = {"topic": ""}  # Missing required fields
        
        with pytest.raises(ValidationError) as exc_info:
            service.process_event(invalid_data)
        
        assert exc_info.value.code == "VALIDATION_INVALID_REQUEST"
    
    def test_process_event_already_processed(self, mock_database_port, sample_event_data):
        """Test processing already processed event."""
        service = EventProcessingService(mock_database_port)
        
        # Mock existing processed event
        mock_event = Mock()
        mock_event.processed = True
        mock_database_port.get_event.return_value = mock_event
        
        result = service.process_event(sample_event_data)
        
        assert result["success"] is False
        assert "already been processed" in result["error"]
        mock_database_port.save_event.assert_not_called()
    
    def test_process_events_batch_success(self, mock_database_port, sample_batch_events):
        """Test successful batch event processing."""
        service = EventProcessingService(mock_database_port)
        
        # Mock database calls
        mock_database_port.save_events_batch.return_value = ["id-1", "id-2"]
        
        result = service.process_events_batch(sample_batch_events)
        
        assert result["success"] is True
        assert result["count"] == 2
        assert result["event_ids"] == ["id-1", "id-2"]
        mock_database_port.save_events_batch.assert_called_once()
        mock_database_port.mark_event_processed.assert_any_call("id-1")
        mock_database_port.mark_event_processed.assert_any_call("id-2")
    
    def test_process_events_batch_validation_error(self, mock_database_port):
        """Test batch processing with invalid data."""
        service = EventProcessingService(mock_database_port)
        
        invalid_batch = [{"topic": ""}]  # Invalid event
        
        with pytest.raises(ValidationError) as exc_info:
            service.process_events_batch(invalid_batch)
        
        assert exc_info.value.code == "VALIDATION_INVALID_REQUEST"
    
    def test_get_event_success(self, mock_database_port):
        """Test successful event retrieval."""
        service = EventProcessingService(mock_database_port)
        
        # Mock event
        mock_event = Mock()
        mock_event.event_id = "test-id"
        mock_event.topic = "test-topic"
        mock_event.partition = 0
        mock_event.offset = 123
        mock_event.key = "test-key"
        mock_event.value = {"data": "test"}
        mock_event.timestamp = datetime.now()
        mock_event.headers = {"source": "test"}
        mock_event.processed = True
        mock_event.error = None
        mock_event.created_at = datetime.now()
        
        mock_database_port.get_event.return_value = mock_event
        
        result = service.get_event("test-id")
        
        assert result is not None
        assert result["event_id"] == "test-id"
        assert result["topic"] == "test-topic"
        assert result["processed"] is True
        mock_database_port.get_event.assert_called_once_with("test-id")
    
    def test_get_event_not_found(self, mock_database_port):
        """Test event retrieval when not found."""
        service = EventProcessingService(mock_database_port)
        
        mock_database_port.get_event.return_value = None
        
        result = service.get_event("non-existent-id")
        
        assert result is None
        mock_database_port.get_event.assert_called_once_with("non-existent-id")
    
    def test_query_events_success(self, mock_database_port):
        """Test successful event querying."""
        service = EventProcessingService(mock_database_port)
        
        # Mock events
        mock_event = Mock()
        mock_event.event_id = "test-id"
        mock_event.topic = "test-topic"
        mock_event.partition = 0
        mock_event.offset = 123
        mock_event.key = "test-key"
        mock_event.value = {"data": "test"}
        mock_event.timestamp = datetime.now()
        mock_event.headers = {}
        mock_event.processed = False
        mock_event.error = None
        mock_event.created_at = datetime.now()
        
        mock_database_port.get_events_by_topic.return_value = [mock_event]
        
        result = service.query_events({"topic": "test-topic", "limit": 10, "offset": 0})
        
        assert result["count"] == 1
        assert len(result["events"]) == 1
        assert result["events"][0]["event_id"] == "test-id"
        mock_database_port.get_events_by_topic.assert_called_once_with("test-topic", 10, 0)
    
    def test_query_events_invalid_pagination(self, mock_database_port):
        """Test event querying with invalid pagination."""
        service = EventProcessingService(mock_database_port)
        
        with pytest.raises(ValidationError) as exc_info:
            service.query_events({"limit": 0})  # Invalid limit
        
        assert exc_info.value.code == "VALIDATION_INVALID_REQUEST"
    
    def test_update_consumer_offset_success(self, mock_database_port, sample_consumer_offset_data):
        """Test successful consumer offset update."""
        service = EventProcessingService(mock_database_port)
        
        mock_database_port.save_consumer_offset.return_value = True
        
        result = service.update_consumer_offset(sample_consumer_offset_data)
        
        assert result["consumer_group"] == "test-group"
        assert result["topic"] == "test-topic"
        assert result["partition"] == 0
        assert result["offset"] == 123
        mock_database_port.save_consumer_offset.assert_called_once()
    
    def test_update_consumer_offset_validation_error(self, mock_database_port):
        """Test consumer offset update with invalid data."""
        service = EventProcessingService(mock_database_port)
        
        invalid_data = {"consumer_group": "test"}  # Missing required fields
        
        with pytest.raises(ValidationError) as exc_info:
            service.update_consumer_offset(invalid_data)
        
        assert exc_info.value.code == "VALIDATION_MISSING_FIELD"
    
    def test_update_consumer_offset_failure(self, mock_database_port, sample_consumer_offset_data):
        """Test consumer offset update failure."""
        service = EventProcessingService(mock_database_port)
        
        mock_database_port.save_consumer_offset.return_value = False
        
        with pytest.raises(BusinessError) as exc_info:
            service.update_consumer_offset(sample_consumer_offset_data)
        
        assert exc_info.value.code == "BUSINESS_PROCESSING_FAILED"
