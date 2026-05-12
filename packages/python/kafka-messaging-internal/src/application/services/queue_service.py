"""Queue service with single responsibility."""

import logging
from typing import Any, Dict, List, Optional
from opentelemetry import trace

from shared.ports.queue_port import QueuePort

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


class QueueService:
    """Service for queue operations with single responsibility"""
    
    def __init__(self, queue: QueuePort):
        self._queue = queue
    
    async def enqueue_event(self, queue_name: str, event_data: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Enqueue event for processing"""
        with _tracer.start_as_current_span("enqueue_event") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "queue-management")
            span.set_attribute("api.version", "v1")
            span.set_attribute("queue.name", queue_name)
            
            try:
                message_id = self._queue.enqueue(queue_name, event_data, metadata)
                span.set_attribute("queue.result", "enqueued")
                span.set_attribute("queue.message_id", message_id)
                logger.info("event=queue_enqueue queue=%s message_id=%s", queue_name, message_id)
                return message_id
            except Exception as e:
                span.record_error(e)
                span.set_attribute("queue.result", "error")
                logger.error("event=queue_enqueue_failed queue=%s error=%s", queue_name, str(e))
                raise
    
    async def dequeue_event(self, queue_name: str, timeout: Optional[int] = 30) -> Optional[Any]:
        """Dequeue event for processing"""
        with _tracer.start_as_current_span("dequeue_event") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "queue-management")
            span.set_attribute("api.version", "v1")
            span.set_attribute("queue.name", queue_name)
            
            try:
                message = self._queue.dequeue(queue_name, timeout)
                if message:
                    span.set_attribute("queue.result", "dequeued")
                    logger.info("event=queue_dequeue queue=%s", queue_name)
                else:
                    span.set_attribute("queue.result", "empty")
                    logger.debug("event=queue_empty queue=%s", queue_name)
                
                return message
            except Exception as e:
                span.record_error(e)
                span.set_attribute("queue.result", "error")
                logger.error("event=queue_dequeue_failed queue=%s error=%s", queue_name, str(e))
                raise
    
    async def dequeue_batch(self, queue_name: str, batch_size: int = 10, timeout: Optional[int] = 30) -> List[Any]:
        """Dequeue multiple events for batch processing"""
        with _tracer.start_as_current_span("dequeue_batch") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "queue-management")
            span.set_attribute("api.version", "v1")
            span.set_attribute("queue.name", queue_name)
            span.set_attribute("queue.batch_size", batch_size)
            
            try:
                messages = self._queue.dequeue_batch(queue_name, batch_size, timeout)
                span.set_attribute("queue.result", "dequeued_batch")
                span.set_attribute("queue.actual_count", len(messages))
                logger.info("event=queue_dequeue_batch queue=%s count=%d", queue_name, len(messages))
                return messages
            except Exception as e:
                span.record_error(e)
                span.set_attribute("queue.result", "error")
                logger.error("event=queue_dequeue_batch_failed queue=%s error=%s", queue_name, str(e))
                raise
    
    async def acknowledge_event(self, queue_name: str, message_id: str) -> bool:
        """Acknowledge successful event processing"""
        with _tracer.start_as_current_span("acknowledge_event") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "queue-management")
            span.set_attribute("api.version", "v1")
            span.set_attribute("queue.name", queue_name)
            span.set_attribute("queue.message_id", message_id)
            
            try:
                success = self._queue.acknowledge(queue_name, message_id)
                span.set_attribute("queue.result", "acknowledged" if success else "ack_failed")
                logger.info("event=queue_acknowledge queue=%s message_id=%s success=%s", queue_name, message_id, success)
                return success
            except Exception as e:
                span.record_error(e)
                span.set_attribute("queue.result", "error")
                logger.error("event=queue_acknowledge_failed queue=%s message_id=%s error=%s", queue_name, message_id, str(e))
                raise
    
    async def reject_event(self, queue_name: str, message_id: str, requeue: bool = True) -> bool:
        """Reject event processing"""
        with _tracer.start_as_current_span("reject_event") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "queue-management")
            span.set_attribute("api.version", "v1")
            span.set_attribute("queue.name", queue_name)
            span.set_attribute("queue.message_id", message_id)
            span.set_attribute("queue.requeue", requeue)
            
            try:
                success = self._queue.reject(queue_name, message_id, requeue)
                span.set_attribute("queue.result", "rejected" if success else "reject_failed")
                logger.info("event=queue_reject queue=%s message_id=%s requeue=%s success=%s", queue_name, message_id, requeue, success)
                return success
            except Exception as e:
                span.record_error(e)
                span.set_attribute("queue.result", "error")
                logger.error("event=queue_reject_failed queue=%s message_id=%s error=%s", queue_name, message_id, str(e))
                raise
    
    def get_queue_size(self, queue_name: str) -> int:
        """Get current queue size"""
        with _tracer.start_as_current_span("get_queue_size") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "queue-management")
            span.set_attribute("api.version", "v1")
            span.set_attribute("queue.name", queue_name)
            
            try:
                size = self._queue.get_queue_size(queue_name)
                span.set_attribute("queue.result", "size_retrieved")
                span.set_attribute("queue.size", size)
                logger.debug("event=queue_size queue=%s size=%d", queue_name, size)
                return size
            except Exception as e:
                span.record_error(e)
                span.set_attribute("queue.result", "error")
                logger.error("event=queue_size_failed queue=%s error=%s", queue_name, str(e))
                raise
    
    async def purge_queue(self, queue_name: str) -> int:
        """Purge all messages from queue"""
        with _tracer.start_as_current_span("purge_queue") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "queue-management")
            span.set_attribute("api.version", "v1")
            span.set_attribute("queue.name", queue_name)
            
            try:
                count = self._queue.purge_queue(queue_name)
                span.set_attribute("queue.result", "purged")
                span.set_attribute("queue.purged_count", count)
                logger.info("event=queue_purge queue=%s count=%d", queue_name, count)
                return count
            except Exception as e:
                span.record_error(e)
                span.set_attribute("queue.result", "error")
                logger.error("event=queue_purge_failed queue=%s error=%s", queue_name, str(e))
                raise
    
    def close(self):
        """Close queue service"""
        self._queue.close()
        logger.info("event=queue_service_closed")
