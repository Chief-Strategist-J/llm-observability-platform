"""Producer client with single responsibility."""

import logging
from typing import List, Dict, Any, Optional
from opentelemetry import trace

from shared.errors.codes import http_request_failed

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


class ProducerClient:
    """Client for producer operations with single responsibility"""
    
    def __init__(self, base_client):
        self._client = base_client
        self._base_path = "/api/v1/producer"
    
    def produce_message(self, topic: str, value: Any, key: Optional[str] = None,
                       partition: Optional[int] = None, 
                       headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Produce single message"""
        with _tracer.start_as_current_span("produce_message") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "producer-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("topic.name", topic)
            
            try:
                data = {
                    "topic": topic,
                    "key": key,
                    "value": value,
                    "partition": partition,
                    "headers": headers or {}
                }
                result = self._client.post(f"{self._base_path}/produce", data=data)
                span.set_attribute("client.result", "success")
                span.set_attribute("message.id", result.get("message_id", ""))
                logger.info("event=message_produced topic=%s id=%s", topic, result.get("message_id", ""))
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=message_produce_failed topic=%s error=%s", topic, str(e))
                raise http_request_failed(f"Failed to produce message: {str(e)}")
    
    def produce_messages_batch(self, messages: List[Dict]) -> Dict[str, Any]:
        """Produce messages in batch"""
        with _tracer.start_as_current_span("produce_messages_batch") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "producer-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("messages.count", str(len(messages)))
            
            try:
                data = {"messages": messages}
                result = self._client.post(f"{self._base_path}/produce/batch", data=data)
                span.set_attribute("client.result", "success")
                span.set_attribute("produced.count", str(len(result.get("produced_messages", []))))
                logger.info("event=messages_produced_batch input=%d produced=%d", len(messages), len(result.get("produced_messages", [])))
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=messages_produce_batch_failed count=%d error=%s", len(messages), str(e))
                raise http_request_failed(f"Failed to produce messages batch: {str(e)}")
    
    def list_topics(self) -> Dict[str, List[str]]:
        """List all topics"""
        with _tracer.start_as_current_span("list_topics") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "producer-client")
            span.set_attribute("api.version", "v1")
            
            try:
                result = self._client.get(f"{self._base_path}/topics")
                topics = result.get("topics", [])
                span.set_attribute("client.result", "success")
                span.set_attribute("topics.count", str(len(topics)))
                logger.info("event=topics_listed count=%d", len(topics))
                return {"topics": topics}
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=topics_list_failed error=%s", str(e))
                raise http_request_failed(f"Failed to list topics: {str(e)}")
    
    def create_topic(self, topic_name: str, partitions: int = 1,
                    replication_factor: int = 1) -> Dict[str, bool]:
        """Create new topic"""
        with _tracer.start_as_current_span("create_topic") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "producer-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("topic.name", topic_name)
            span.set_attribute("partitions", str(partitions))
            span.set_attribute("replication.factor", str(replication_factor))
            
            try:
                data = {
                    "topic_name": topic_name,
                    "partitions": partitions,
                    "replication_factor": replication_factor
                }
                result = self._client.post(f"{self._base_path}/topics", data=data)
                span.set_attribute("client.result", "success")
                logger.info("event=topic_created name=%s partitions=%d replication=%d", topic_name, partitions, replication_factor)
                return {"success": True}
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=topic_create_failed name=%s error=%s", topic_name, str(e))
                raise http_request_failed(f"Failed to create topic: {str(e)}")
    
    def flush_producer(self) -> Dict[str, bool]:
        """Flush producer"""
        with _tracer.start_as_current_span("flush_producer") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "producer-client")
            span.set_attribute("api.version", "v1")
            
            try:
                result = self._client.post(f"{self._base_path}/flush")
                span.set_attribute("client.result", "success")
                logger.info("event=producer_flushed")
                return {"success": True}
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=producer_flush_failed error=%s", str(e))
                raise http_request_failed(f"Failed to flush producer: {str(e)}")
    
    def get_producer_metrics(self) -> Dict[str, Any]:
        """Get producer metrics"""
        with _tracer.start_as_current_span("get_producer_metrics") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "producer-client")
            span.set_attribute("api.version", "v1")
            
            try:
                result = self._client.get(f"{self._base_path}/metrics")
                span.set_attribute("client.result", "success")
                logger.info("event=producer_metrics_retrieved")
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=producer_metrics_retrieve_failed error=%s", str(e))
                raise http_request_failed(f"Failed to get producer metrics: {str(e)}")
    
    def close(self):
        """Close client"""
        with _tracer.start_as_current_span("close_producer_client") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "producer-client")
            span.set_attribute("api.version", "v1")
            
            try:
                self._client.close()
                span.set_attribute("close.result", "success")
                logger.info("event=producer_client_closed")
            except Exception as e:
                span.record_error(e)
                span.set_attribute("close.result", "failed")
                logger.error("event=producer_client_close_error error=%s", str(e))
