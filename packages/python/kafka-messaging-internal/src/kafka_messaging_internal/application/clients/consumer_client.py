"""Consumer client with single responsibility."""

import logging
from typing import List, Dict, Any, Optional
from opentelemetry import trace

from shared.errors.codes import http_request_failed

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


class ConsumerClient:
    """Client for consumer operations with single responsibility"""
    
    def __init__(self, base_client):
        self._client = base_client
        self._base_path = "/api/v1/consumer"
    
    def consume_messages(self, topic: str, consumer_group: str,
                         partition: Optional[int] = None,
                         max_messages: int = 10,
                         timeout_ms: int = 1000) -> Dict[str, Any]:
        """Consume messages from topic"""
        with _tracer.start_as_current_span("consume_messages") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "consumer-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("topic.name", topic)
            span.set_attribute("consumer.group", consumer_group)
            span.set_attribute("max.messages", str(max_messages))
            
            try:
                data = {
                    "topic": topic,
                    "consumer_group": consumer_group,
                    "partition": partition,
                    "max_messages": max_messages,
                    "timeout_ms": timeout_ms
                }
                result = self._client.post(f"{self._base_path}/consume", data=data)
                span.set_attribute("client.result", "success")
                span.set_attribute("messages.count", str(len(result.get("messages", []))))
                logger.info("event=messages_consumed topic=%s group=%s count=%d", topic, consumer_group, len(result.get("messages", [])))
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=messages_consume_failed topic=%s group=%s error=%s", topic, consumer_group, str(e))
                raise http_request_failed(f"Failed to consume messages: {str(e)}")
    
    def consume_parallel(self, topic: str, consumer_group: str,
                       partitions: List[int],
                       max_messages: int = 10,
                       timeout_ms: int = 1000) -> Dict[str, Any]:
        """Consume messages from multiple partitions in parallel"""
        with _tracer.start_as_current_span("consume_parallel") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "consumer-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("topic.name", topic)
            span.set_attribute("consumer.group", consumer_group)
            span.set_attribute("partitions.count", str(len(partitions)))
            
            try:
                data = {
                    "topic": topic,
                    "consumer_group": consumer_group,
                    "partitions": partitions,
                    "max_messages": max_messages,
                    "timeout_ms": timeout_ms
                }
                result = self._client.post(f"{self._base_path}/consume/parallel", data=data)
                span.set_attribute("client.result", "success")
                total_messages = sum(len(msgs) for msgs in result.get("messages", {}).values())
                span.set_attribute("messages.count", str(total_messages))
                logger.info("event=messages_consumed_parallel topic=%s group=%s partitions=%d total=%d", topic, consumer_group, len(partitions), total_messages)
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=messages_consume_parallel_failed topic=%s group=%s error=%s", topic, consumer_group, str(e))
                raise http_request_failed(f"Failed to consume parallel messages: {str(e)}")
    
    def commit_offset(self, consumer_group: str, topic: str,
                     partition: int, offset: int) -> Dict[str, bool]:
        """Commit specific offset"""
        with _tracer.start_as_current_span("commit_offset") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "consumer-client")
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
                result = self._client.post(f"{self._base_path}/commit/offset", data=data)
                span.set_attribute("client.result", "success")
                logger.info("event=offset_committed group=%s topic=%s partition=%d offset=%d", consumer_group, topic, partition, offset)
                return {"success": True}
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=offset_commit_failed group=%s topic=%s partition=%d error=%s", consumer_group, topic, partition, str(e))
                raise http_request_failed(f"Failed to commit offset: {str(e)}")
    
    def commit_offsets(self) -> Dict[str, bool]:
        """Commit all offsets"""
        with _tracer.start_as_current_span("commit_offsets") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "consumer-client")
            span.set_attribute("api.version", "v1")
            
            try:
                result = self._client.post(f"{self._base_path}/commit")
                span.set_attribute("client.result", "success")
                logger.info("event=offsets_committed")
                return {"success": True}
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=offsets_commit_failed error=%s", str(e))
                raise http_request_failed(f"Failed to commit offsets: {str(e)}")
    
    def subscribe_topics(self, topics: List[str]) -> Dict[str, bool]:
        """Subscribe to topics"""
        with _tracer.start_as_current_span("subscribe_topics") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "consumer-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("topics.count", str(len(topics)))
            
            try:
                data = {"topics": topics}
                result = self._client.post(f"{self._base_path}/subscribe", data=data)
                span.set_attribute("client.result", "success")
                logger.info("event=topics_subscribed count=%d", len(topics))
                return {"success": True, "topics": topics}
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=topics_subscribe_failed error=%s", str(e))
                raise http_request_failed(f"Failed to subscribe to topics: {str(e)}")
    
    def unsubscribe_topics(self) -> Dict[str, bool]:
        """Unsubscribe from all topics"""
        with _tracer.start_as_current_span("unsubscribe_topics") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "consumer-client")
            span.set_attribute("api.version", "v1")
            
            try:
                result = self._client.post(f"{self._base_path}/unsubscribe")
                span.set_attribute("client.result", "success")
                logger.info("event=topics_unsubscribed")
                return {"success": True}
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=topics_unsubscribe_failed error=%s", str(e))
                raise http_request_failed(f"Failed to unsubscribe from topics: {str(e)}")
    
    def close(self):
        """Close client"""
        with _tracer.start_as_current_span("close_consumer_client") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "consumer-client")
            span.set_attribute("api.version", "v1")
            
            try:
                self._client.close()
                span.set_attribute("close.result", "success")
                logger.info("event=consumer_client_closed")
            except Exception as e:
                span.record_error(e)
                span.set_attribute("close.result", "failed")
                logger.error("event=consumer_client_close_error error=%s", str(e))
