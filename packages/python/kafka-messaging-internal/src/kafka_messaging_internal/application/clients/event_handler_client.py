"""Event handler client with single responsibility."""

import logging
from typing import List, Dict, Any, Optional
from opentelemetry import trace

from shared.errors.codes import http_request_failed

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


class EventHandlerClient:
    """Client for event handler operations with single responsibility"""
    
    def __init__(self, base_client):
        self._client = base_client
        self._base_path = "/api/v1/event-handler"
    
    def process_record(self, topic: str, partition: int, offset: int,
                       key: Optional[str] = None, value: Optional[Any] = None,
                       timestamp: int = 0, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Process single record"""
        with _tracer.start_as_current_span("process_record") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "event-handler-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("topic.name", topic)
            span.set_attribute("partition", str(partition))
            span.set_attribute("offset", str(offset))
            
            try:
                data = {
                    "topic": topic,
                    "partition": partition,
                    "offset": offset,
                    "key": key,
                    "value": value,
                    "timestamp": timestamp,
                    "headers": headers or {}
                }
                result = self._client.post(f"{self._base_path}/process-record", data=data)
                span.set_attribute("client.result", "success")
                span.set_attribute("record.id", result.get("record_id", ""))
                logger.info("event=record_processed topic=%s partition=%d offset=%d id=%s", topic, partition, offset, result.get("record_id", ""))
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=record_process_failed topic=%s partition=%d offset=%d error=%s", topic, partition, offset, str(e))
                raise http_request_failed(f"Failed to process record: {str(e)}")
    
    def process_records_batch(self, records: List[Dict]) -> Dict[str, Any]:
        """Process records in batch"""
        with _tracer.start_as_current_span("process_records_batch") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "event-handler-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("records.count", str(len(records)))
            
            try:
                data = {"records": records}
                result = self._client.post(f"{self._base_path}/process-records-batch", data=data)
                span.set_attribute("client.result", "success")
                span.set_attribute("processed.count", str(len(result.get("processed_records", []))))
                logger.info("event=records_processed_batch input=%d processed=%d", len(records), len(result.get("processed_records", [])))
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=records_process_batch_failed count=%d error=%s", len(records), str(e))
                raise http_request_failed(f"Failed to process records batch: {str(e)}")
    
    def save_consumer_offset(self, consumer_group: str, topic: str,
                            partition: int, offset: int) -> Dict[str, bool]:
        """Save consumer offset"""
        with _tracer.start_as_current_span("save_consumer_offset") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "event-handler-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("consumer.group", consumer_group)
            span.set_attribute("topic.name", topic)
            span.set_attribute("partition", str(partition))
            span.set_attribute("offset", str(offset))
            
            try:
                data = {
                    "consumer_group": consumer_group,
                    "topic": topic,
                    "partition": partition,
                    "offset": offset
                }
                result = self._client.post(f"{self._base_path}/consumer-offset", data=data)
                span.set_attribute("client.result", "success")
                logger.info("event=consumer_offset_saved group=%s topic=%s partition=%d offset=%d", consumer_group, topic, partition, offset)
                return {"success": True}
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=consumer_offset_save_failed group=%s topic=%s partition=%d error=%s", consumer_group, topic, partition, str(e))
                raise http_request_failed(f"Failed to save consumer offset: {str(e)}")
    
    def get_processing_status(self, record_id: str) -> Dict[str, Any]:
        """Get processing status"""
        with _tracer.start_as_current_span("get_processing_status") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "event-handler-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("record.id", record_id)
            
            try:
                result = self._client.get(f"{self._base_path}/status/{record_id}")
                span.set_attribute("client.result", "success")
                span.set_attribute("status", result.get("status", ""))
                logger.info("event=processing_status_retrieved id=%s status=%s", record_id, result.get("status", ""))
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=processing_status_retrieve_failed id=%s error=%s", record_id, str(e))
                raise http_request_failed(f"Failed to get processing status: {str(e)}")
    
    def retry_failed_records(self, limit: int = 100) -> Dict[str, Any]:
        """Retry failed records"""
        with _tracer.start_as_current_span("retry_failed_records") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "event-handler-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("retry.limit", str(limit))
            
            try:
                data = {"limit": limit}
                result = self._client.post(f"{self._base_path}/retry-failed", data=data)
                span.set_attribute("client.result", "success")
                span.set_attribute("retried.count", str(len(result.get("retried_records", []))))
                logger.info("event=failed_records_retried limit=%d retried=%d", limit, len(result.get("retried_records", [])))
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=failed_records_retry_failed limit=%d error=%s", limit, str(e))
                raise http_request_failed(f"Failed to retry failed records: {str(e)}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get event handler metrics"""
        with _tracer.start_as_current_span("get_event_handler_metrics") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "event-handler-client")
            span.set_attribute("api.version", "v1")
            
            try:
                result = self._client.get(f"{self._base_path}/metrics")
                span.set_attribute("client.result", "success")
                logger.info("event=event_handler_metrics_retrieved")
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=event_handler_metrics_retrieve_failed error=%s", str(e))
                raise http_request_failed(f"Failed to get event handler metrics: {str(e)}")
    
    def close(self):
        """Close client"""
        with _tracer.start_as_current_span("close_event_handler_client") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "event-handler-client")
            span.set_attribute("api.version", "v1")
            
            try:
                self._client.close()
                span.set_attribute("close.result", "success")
                logger.info("event=event_handler_client_closed")
            except Exception as e:
                span.record_error(e)
                span.set_attribute("close.result", "failed")
                logger.error("event=event_handler_client_close_error error=%s", str(e))
