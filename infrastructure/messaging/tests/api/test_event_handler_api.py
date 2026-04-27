import pytest
from unittest.mock import Mock
from fastapi import HTTPException

from application.api.v1.event_handler_api import (
    EventHandlerAPI,
    SchemaAwareEventHandlerAPI,
    ConsumerRecordRequest,
    BatchConsumerRecordRequest,
    ConsumerOffsetRequest,
    SubjectMappingRequest,
    ProcessEventResponse,
    BatchProcessEventResponse,
    ConsumerOffsetResponse
)
from domain.services.event_handler import ConsumerRecord
from application.api.v1.validators import ValidationError


@pytest.fixture
def mock_event_handler():
    return Mock()


@pytest.fixture
def event_handler_api(mock_event_handler):
    return EventHandlerAPI(mock_event_handler)


@pytest.fixture
def mock_schema_aware_handler():
    return Mock()


@pytest.fixture
def schema_aware_api(mock_schema_aware_handler):
    return SchemaAwareEventHandlerAPI(mock_schema_aware_handler)


class TestConsumerRecordRequest:
    def test_valid_request(self):
        request = ConsumerRecordRequest(
            topic="test-topic",
            partition=0,
            offset=1,
            key="test-key",
            value={"data": "test"},
            timestamp=1234567890
        )
        assert request.topic == "test-topic"
        assert request.partition == 0
        assert request.offset == 1







class TestBatchConsumerRecordRequest:
    def test_valid_batch_request(self):
        records = [
            ConsumerRecordRequest(topic="test-topic", partition=0, offset=i, value=f"value-{i}", timestamp=1234567890)
            for i in range(5)
        ]
        request = BatchConsumerRecordRequest(records=records)
        assert len(request.records) == 5




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




class TestSubjectMappingRequest:
    def test_valid_request(self):
        request = SubjectMappingRequest(
            topic="test-topic",
            subject="test-subject"
        )
        assert request.topic == "test-topic"
        assert request.subject == "test-subject"




class TestEventHandlerAPIProcessRecord:
    def test_process_record_success(self, event_handler_api, mock_event_handler):
        request = ConsumerRecordRequest(
            topic="test-topic",
            partition=0,
            offset=1,
            value="test-value",
            timestamp=1234567890
        )
        mock_event_handler.process_kafka_record.return_value = "event-id-123"
        
        response = event_handler_api.process_record(request)
        
        assert response.event_id == "event-id-123"
        assert response.success is True

    def test_process_record_empty_topic_raises_400(self, event_handler_api):
        request = ConsumerRecordRequest(
            topic="",
            partition=0,
            offset=1,
            value="test-value",
            timestamp=1234567890
        )
        
        with pytest.raises(HTTPException) as exc:
            event_handler_api.process_record(request)
        
        assert exc.value.status_code == 400
        assert "topic" in str(exc.value.detail)

    def test_process_record_negative_partition_raises_400(self, event_handler_api):
        request = ConsumerRecordRequest(
            topic="test-topic",
            partition=-1,
            offset=1,
            value="test-value",
            timestamp=1234567890
        )
        
        with pytest.raises(HTTPException) as exc:
            event_handler_api.process_record(request)
        
        assert exc.value.status_code == 400
        assert "partition" in str(exc.value.detail)


class TestEventHandlerAPIProcessRecordsBatch:
    def test_process_records_batch_success(self, event_handler_api, mock_event_handler):
        records = [
            ConsumerRecordRequest(topic="test-topic", partition=0, offset=i, value=f"value-{i}", timestamp=1234567890)
            for i in range(3)
        ]
        request = BatchConsumerRecordRequest(records=records)
        mock_event_handler.process_kafka_records_batch.return_value = ["id-1", "id-2", "id-3"]
        
        response = event_handler_api.process_records_batch(request)
        
        assert response.count == 3
        assert response.success is True

    def test_process_records_batch_empty_list_raises_400(self, event_handler_api):
        request = BatchConsumerRecordRequest(records=[])
        
        with pytest.raises(HTTPException) as exc:
            event_handler_api.process_records_batch(request)
        
        assert exc.value.status_code == 400
        assert "records" in str(exc.value.detail)


class TestEventHandlerAPISaveConsumerOffset:
    def test_save_consumer_offset_success(self, event_handler_api, mock_event_handler):
        request = ConsumerOffsetRequest(
            consumer_group="test-group",
            topic="test-topic",
            partition=0,
            offset=100
        )
        mock_event_handler.save_consumer_offset.return_value = True
        
        response = event_handler_api.save_consumer_offset(request)
        
        assert response["success"] is True

    def test_save_consumer_offset_empty_group_raises_400(self, event_handler_api):
        request = ConsumerOffsetRequest(
            consumer_group="",
            topic="test-topic",
            partition=0,
            offset=100
        )
        
        with pytest.raises(HTTPException) as exc:
            event_handler_api.save_consumer_offset(request)
        
        assert exc.value.status_code == 400
        assert "consumer_group" in str(exc.value.detail)


class TestEventHandlerAPIGetConsumerOffset:
    def test_get_consumer_offset_success(self, event_handler_api, mock_event_handler):
        mock_event_handler.get_consumer_offset.return_value = 100
        
        response = event_handler_api.get_consumer_offset("test-group", "test-topic", 0)
        
        assert response.consumer_group == "test-group"
        assert response.offset == 100

    def test_get_consumer_offset_empty_group_raises_400(self, event_handler_api):
        with pytest.raises(HTTPException) as exc:
            event_handler_api.get_consumer_offset("", "test-topic", 0)
        
        assert exc.value.status_code == 400
        assert "consumer_group" in str(exc.value.detail)

    def test_get_consumer_offset_not_found_raises_404(self, event_handler_api, mock_event_handler):
        mock_event_handler.get_consumer_offset.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            event_handler_api.get_consumer_offset("test-group", "test-topic", 0)
        
        assert exc.value.status_code == 404


class TestEventHandlerAPIGetEventsByTopic:
    def test_get_events_by_topic_success(self, event_handler_api, mock_event_handler):
        from domain.ports.database_port import EventRecord
        from datetime import datetime
        events = [
            EventRecord(topic="test-topic", partition=0, offset=i, key=str(i), value=f"value-{i}", timestamp=datetime.now())
            for i in range(3)
        ]
        mock_event_handler.get_events_by_topic.return_value = events
        
        response = event_handler_api.get_events_by_topic("test-topic", limit=10, offset=0)
        
        assert len(response) == 3

    def test_get_events_by_topic_empty_topic_raises_400(self, event_handler_api):
        with pytest.raises(HTTPException) as exc:
            event_handler_api.get_events_by_topic("", limit=10, offset=0)
        
        assert exc.value.status_code == 400
        assert "topic" in str(exc.value.detail)


class TestSchemaAwareEventHandlerAPIRegisterSubjectMapping:
    def test_register_subject_mapping_success(self, schema_aware_handler_api, mock_schema_aware_handler):
        request = SubjectMappingRequest(
            topic="test-topic",
            subject="test-subject"
        )
        
        response = schema_aware_handler_api.register_subject_mapping(request)
        
        assert response["success"] is True

    def test_register_subject_mapping_empty_topic_raises_400(self, schema_aware_handler_api):
        request = SubjectMappingRequest(
            topic="",
            subject="test-subject"
        )
        
        with pytest.raises(HTTPException) as exc:
            schema_aware_handler_api.register_subject_mapping(request)
        
        assert exc.value.status_code == 400
        assert "topic" in str(exc.value.detail)


class TestSchemaAwareEventHandlerAPIProcessRecord:
    def test_process_record_success(self, schema_aware_handler_api, mock_schema_aware_handler):
        request = ConsumerRecordRequest(
            topic="test-topic",
            partition=0,
            offset=1,
            value="test-value",
            timestamp=1234567890
        )
        mock_schema_aware_handler.process_kafka_record.return_value = "event-id-123"
        
        response = schema_aware_handler_api.process_record(request)
        
        assert response.event_id == "event-id-123"

    def test_process_record_empty_topic_raises_400(self, schema_aware_handler_api):
        request = ConsumerRecordRequest(
            topic="",
            partition=0,
            offset=1,
            value="test-value",
            timestamp=1234567890
        )
        
        with pytest.raises(HTTPException) as exc:
            schema_aware_handler_api.process_record(request)
        
        assert exc.value.status_code == 400
        assert "topic" in str(exc.value.detail)


class TestSchemaAwareEventHandlerAPISerializeAndProduce:
    def test_serialize_and_produce_success(self, schema_aware_handler_api, mock_schema_aware_handler):
        mock_schema_aware_handler.serialize_and_produce.return_value = b"serialized-data"
        
        response = schema_aware_handler_api.serialize_and_produce("test-topic", {"key": "value"})
        
        assert response["data"] is not None

    def test_serialize_and_produce_empty_topic_raises_400(self, schema_aware_handler_api):
        with pytest.raises(HTTPException) as exc:
            schema_aware_handler_api.serialize_and_produce("", {"key": "value"})
        
        assert exc.value.status_code == 400
        assert "topic" in str(exc.value.detail)

    def test_serialize_and_produce_none_data_raises_400(self, schema_aware_handler_api):
        with pytest.raises(HTTPException) as exc:
            schema_aware_handler_api.serialize_and_produce("test-topic", None)
        
        assert exc.value.status_code == 400
        assert "data" in str(exc.value.detail)



class TestEventHandlerAPIGetEventCount:
    def test_get_event_count_success(self, event_handler_api, mock_event_handler):
        mock_event_handler.get_event_count.return_value = 100
        
        response = event_handler_api.get_event_count("test-topic")
        
        assert response["count"] == 100

    def test_get_event_count_without_topic(self, event_handler_api, mock_event_handler):
        mock_event_handler.get_event_count.return_value = 500
        
        response = event_handler_api.get_event_count(None)
        
        assert response["count"] == 500


class TestSchemaAwareEventHandlerAPIRegisterSubjectMapping:
    def test_register_subject_mapping_success(self, schema_aware_api, mock_schema_aware_handler):
        request = SubjectMappingRequest(
            topic="test-topic",
            subject="test-subject"
        )
        
        response = schema_aware_api.register_subject_mapping(request)
        
        assert response["success"] is True
        mock_schema_aware_handler.register_subject_mapping.assert_called_once()



class TestSchemaAwareEventHandlerAPIProcessRecord:
    def test_process_record_success(self, schema_aware_api, mock_schema_aware_handler):
        request = ConsumerRecordRequest(
            topic="test-topic",
            partition=0,
            offset=1,
            value="test-value",
            timestamp=1234567890
        )
        mock_schema_aware_handler.process_kafka_record.return_value = "event-id-123"
        
        response = schema_aware_api.process_record(request, deserialize=True)
        
        assert response.event_id == "event-id-123"
        assert response.success is True



class TestSchemaAwareEventHandlerAPIProcessRecordsBatch:
    def test_process_records_batch_success(self, schema_aware_api, mock_schema_aware_handler):
        records = [
            ConsumerRecordRequest(topic="test-topic", partition=0, offset=i, value=f"value-{i}", timestamp=1234567890)
            for i in range(3)
        ]
        request = BatchConsumerRecordRequest(records=records)
        mock_schema_aware_handler.process_kafka_records_batch.return_value = ["id-1", "id-2", "id-3"]
        
        response = schema_aware_api.process_records_batch(request, deserialize=True)
        
        assert response.count == 3
        assert response.success is True


class TestSchemaAwareEventHandlerAPISerializeAndProduce:
    def test_serialize_and_produce_success(self, schema_aware_api, mock_schema_aware_handler):
        mock_schema_aware_handler.serialize_and_produce.return_value = b"serialized-data"
        
        response = schema_aware_api.serialize_and_produce("test-topic", {"key": "value"})
        
        assert response["data"] is not None
        mock_schema_aware_handler.serialize_and_produce.assert_called_once()



class TestSchemaAwareEventHandlerAPIListRegisteredSubjects:
    def test_list_registered_subjects_success(self, schema_aware_api, mock_schema_aware_handler):
        mock_schema_aware_handler.list_registered_subjects.return_value = ["subject1", "subject2"]
        
        response = schema_aware_api.list_registered_subjects()
        
        assert response["subjects"] == ["subject1", "subject2"]

    def test_list_registered_subjects_error_raises_500(self, schema_aware_api, mock_schema_aware_handler):
        mock_schema_aware_handler.list_registered_subjects.side_effect = Exception("Handler error")
        
        with pytest.raises(HTTPException) as exc:
            schema_aware_api.list_registered_subjects()
        
        assert exc.value.status_code == 500


class TestSchemaAwareEventHandlerAPISaveConsumerOffset:
    def test_save_consumer_offset_success(self, schema_aware_api, mock_schema_aware_handler):
        request = ConsumerOffsetRequest(
            consumer_group="test-group",
            topic="test-topic",
            partition=0,
            offset=100
        )
        mock_schema_aware_handler.save_consumer_offset.return_value = True
        
        response = schema_aware_api.save_consumer_offset(request)
        
        assert response["success"] is True



class TestSchemaAwareEventHandlerAPIGetConsumerOffset:
    def test_get_consumer_offset_success(self, schema_aware_api, mock_schema_aware_handler):
        mock_schema_aware_handler.get_consumer_offset.return_value = 100
        
        response = schema_aware_api.get_consumer_offset("test-group", "test-topic", 0)
        
        assert response.consumer_group == "test-group"
        assert response.offset == 100

    def test_get_consumer_offset_not_found_raises_404(self, schema_aware_api, mock_schema_aware_handler):
        mock_schema_aware_handler.get_consumer_offset.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            schema_aware_api.get_consumer_offset("test-group", "test-topic", 0)
        
        assert exc.value.status_code == 404

