import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone

from kafka_messaging_internal.features.event_processing.service import EventProcessingService, ProcessingResult


class TestEventProcessingService:

    @pytest.mark.asyncio
    async def test_process_event_success(self, mock_database_port, sample_event_data):
        service = EventProcessingService(mock_database_port)

        mock_database_port.get_event.return_value = None
        mock_database_port.save_event.return_value = "test-event-id"

        result = await service.process_event(sample_event_data)

        assert result["success"] is True
        assert result["event_id"] == "test-event-id"
        assert result["error"] is None
        mock_database_port.save_event.assert_called_once()
        mock_database_port.mark_event_processed.assert_called_once_with("test-event-id", None)

    @pytest.mark.asyncio
    async def test_process_event_missing_topic(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        invalid_data = {"topic": "", "value": {"data": "test"}}

        result = await service.process_event(invalid_data)

        assert result["success"] is False
        assert result["error"] is not None
        assert "topic" in result["error"].lower()
        mock_database_port.save_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_event_missing_value(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        invalid_data = {"topic": "test-topic"}

        result = await service.process_event(invalid_data)

        assert result["success"] is False
        assert result["error"] is not None
        assert "value" in result["error"].lower()
        mock_database_port.save_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_event_empty_data(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        result = await service.process_event({})

        assert result["success"] is False
        assert result["error"] is not None

    @pytest.mark.asyncio
    async def test_process_event_database_failure(self, mock_database_port, sample_event_data):
        service = EventProcessingService(mock_database_port)

        mock_database_port.save_event.side_effect = Exception("DB connection lost")

        result = await service.process_event(sample_event_data)

        assert result["success"] is False
        assert "DB connection lost" in result["error"]

    @pytest.mark.asyncio
    async def test_process_events_batch_success(self, mock_database_port, sample_batch_events):
        service = EventProcessingService(mock_database_port)

        mock_database_port.save_event.return_value = "batch-event-id"

        results = await service.process_events_batch(sample_batch_events)

        assert isinstance(results, list)
        assert len(results) == 2
        for r in results:
            assert r["success"] is True

    @pytest.mark.asyncio
    async def test_process_events_batch_partial_failure(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        # Batch save will return list of dummy IDs (though not strictly needed anymore)
        mock_database_port.save_events_batch.return_value = ["event-id-1", "event-id-3"]

        events = [
            {"topic": "t", "value": {"d": 1}},
            {"topic": "", "value": {"d": 2}}, # Empty topic causes validation error
            {"topic": "t", "value": {"d": 3}},
        ]

        results = await service.process_events_batch(events)

        assert len(results) == 3
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert "validation" in results[1]["metadata"]["error_type"]
        assert results[2]["success"] is True

    @pytest.mark.asyncio
    async def test_get_event_success(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        mock_event = Mock()
        mock_event.event_id = "test-id"
        mock_event.topic = "test-topic"
        mock_event.value = {"data": "test"}
        mock_event.timestamp = datetime.now(timezone.utc)
        mock_database_port.get_event.return_value = mock_event

        result = await service.get_event("test-id")

        assert result is not None
        assert result["event_id"] == "test-id"
        assert result["topic"] == "test-topic"
        mock_database_port.get_event.assert_called_once_with("test-id")

    @pytest.mark.asyncio
    async def test_get_event_not_found(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        mock_database_port.get_event.return_value = None

        result = await service.get_event("non-existent-id")

        assert result is None
        mock_database_port.get_event.assert_called_once_with("non-existent-id")

    @pytest.mark.asyncio
    async def test_query_events_success(self, mock_database_port):
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

        mock_database_port.get_events_by_topic.return_value = [mock_event]

        events = await service.query_events({"topic": "test-topic", "limit": 10, "offset": 0})

        assert isinstance(events, list)
        assert len(events) == 1
        mock_database_port.get_events_by_topic.assert_called_once_with("test-topic", 10, 0)

    @pytest.mark.asyncio
    async def test_query_events_invalid_limit_zero(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        from kafka_messaging_internal.shared.errors.exceptions import ValidationError
        with pytest.raises((ValidationError, Exception)):
            await service.query_events({"limit": 0})

    @pytest.mark.asyncio
    async def test_query_events_invalid_limit_negative(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        from kafka_messaging_internal.shared.errors.exceptions import ValidationError
        with pytest.raises((ValidationError, Exception)):
            await service.query_events({"limit": -5})

    @pytest.mark.asyncio
    async def test_query_events_limit_exceeds_max(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        from kafka_messaging_internal.shared.errors.exceptions import ValidationError
        with pytest.raises((ValidationError, Exception)):
            await service.query_events({"limit": 1001})

    @pytest.mark.asyncio
    async def test_query_events_negative_offset(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        from kafka_messaging_internal.shared.errors.exceptions import ValidationError
        with pytest.raises((ValidationError, Exception)):
            await service.query_events({"limit": 10, "offset": -1})

    @pytest.mark.asyncio
    async def test_update_consumer_offset_success(self, mock_database_port, sample_consumer_offset_data):
        service = EventProcessingService(mock_database_port)

        mock_database_port.save_consumer_offset.return_value = True

        result = await service.update_consumer_offset(sample_consumer_offset_data)

        assert isinstance(result, ProcessingResult)
        assert result.success is True
        mock_database_port.save_consumer_offset.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_consumer_offset_missing_group(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        invalid_data = {"topic": "t", "partition": 0, "offset": 10}

        result = await service.update_consumer_offset(invalid_data)

        assert isinstance(result, ProcessingResult)
        assert result.success is False

    @pytest.mark.asyncio
    async def test_update_consumer_offset_missing_topic(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        invalid_data = {"consumer_group": "g", "partition": 0, "offset": 10}

        result = await service.update_consumer_offset(invalid_data)

        assert isinstance(result, ProcessingResult)
        assert result.success is False

    @pytest.mark.asyncio
    async def test_update_consumer_offset_negative_partition(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        invalid_data = {"consumer_group": "g", "topic": "t", "partition": -1, "offset": 10}

        result = await service.update_consumer_offset(invalid_data)

        assert isinstance(result, ProcessingResult)
        assert result.success is False

    @pytest.mark.asyncio
    async def test_update_consumer_offset_negative_offset(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        invalid_data = {"consumer_group": "g", "topic": "t", "partition": 0, "offset": -1}

        result = await service.update_consumer_offset(invalid_data)

        assert isinstance(result, ProcessingResult)
        assert result.success is False

    @pytest.mark.asyncio
    async def test_mark_event_processed_success(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        mock_database_port.mark_event_processed.return_value = True

        result = await service.mark_event_processed("test-id")

        assert result is True
        mock_database_port.mark_event_processed.assert_called_once_with("test-id", None)

    @pytest.mark.asyncio
    async def test_mark_event_processed_with_error(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        mock_database_port.mark_event_processed.return_value = True

        result = await service.mark_event_processed("test-id", error="processing failed")

        assert result is True
        mock_database_port.mark_event_processed.assert_called_once_with("test-id", "processing failed")

    @pytest.mark.asyncio
    async def test_mark_event_processed_empty_id(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        from kafka_messaging_internal.shared.errors.exceptions import ValidationError
        with pytest.raises((ValidationError, Exception)):
            await service.mark_event_processed("")

    @pytest.mark.asyncio
    async def test_mark_event_processed_whitespace_id(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        from kafka_messaging_internal.shared.errors.exceptions import ValidationError
        with pytest.raises((ValidationError, Exception)):
            await service.mark_event_processed("   ")

    @pytest.mark.asyncio
    async def test_get_consumer_offsets_with_group_and_topic(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        mock_offset = Mock()
        mock_offset.consumer_group = "g"
        mock_offset.topic = "t"
        mock_offset.partition = 0
        mock_offset.offset = 42
        mock_offset.updated_at = datetime.now(timezone.utc)
        mock_database_port.get_consumer_offset.return_value = mock_offset

        result = await service.get_consumer_offsets({"consumer_group": "g", "topic": "t"})

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].offset == 42

    @pytest.mark.asyncio
    async def test_get_consumer_offsets_incomplete_filter(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        result = await service.get_consumer_offsets({"consumer_group": "g"})

        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_processing_stats(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        stats = await service.get_processing_stats()

        assert "total_events_processed" in stats
        assert "success_rate" in stats

    @pytest.mark.asyncio
    async def test_get_processing_stats_with_topic(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        stats = await service.get_processing_stats("my-topic")

        assert stats["topic"] == "my-topic"

    @pytest.mark.asyncio
    async def test_get_processing_stats_empty_topic(self, mock_database_port):
        service = EventProcessingService(mock_database_port)

        from kafka_messaging_internal.shared.errors.exceptions import ValidationError
        with pytest.raises((ValidationError, Exception)):
            await service.get_processing_stats("   ")
