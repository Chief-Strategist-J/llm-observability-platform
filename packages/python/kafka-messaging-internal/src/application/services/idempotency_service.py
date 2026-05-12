"""Idempotency service with single responsibility."""

import logging
from typing import Any, Optional
from opentelemetry import trace

from shared.ports.idempotency_port import IdempotencyPort

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


class IdempotencyService:
    """Service for idempotency operations with single responsibility"""
    
    def __init__(self, idempotency_store: IdempotencyPort):
        self._idempotency_store = idempotency_store
    
    async def check_and_process(self, key: str, processor, ttl: Optional[int] = 3600) -> tuple[bool, Any]:
        """Check if operation was already performed and process if not"""
        with _tracer.start_as_current_span("check_and_process") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "idempotency")
            span.set_attribute("api.version", "v1")
            span.set_attribute("idempotency.key", key)
            
            try:
                # Check if key exists
                if self._idempotency_store.exists(key):
                    span.set_attribute("idempotency.result", "already_processed")
                    logger.info("event=idempotency_skip key=%s", key)
                    return True, self._idempotency_store.get(key)
                
                # Process the operation
                result = await processor()
                
                # Store the result with TTL
                success = self._idempotency_store.check_and_set(key, result, ttl)
                
                if success:
                    span.set_attribute("idempotency.result", "processed_success")
                    logger.info("event=idempotency_process key=%s", key)
                    return False, result
                else:
                    span.set_attribute("idempotency.result", "race_condition")
                    logger.warning("event=idempotency_race key=%s", key)
                    # Race condition - another process beat us to it
                    return True, self._idempotency_store.get(key)
                    
            except Exception as e:
                span.record_error(e)
                span.set_attribute("idempotency.result", "error")
                logger.error("event=idempotency_error key=%s error=%s", key, str(e))
                raise
    
    def is_processed(self, key: str) -> bool:
        """Check if operation was already processed"""
        with _tracer.start_as_current_span("is_processed") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "idempotency")
            span.set_attribute("api.version", "v1")
            span.set_attribute("idempotency.key", key)
            
            try:
                result = self._idempotency_store.exists(key)
                span.set_attribute("idempotency.result", "checked")
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("idempotency.result", "error")
                logger.error("event=idempotency_check_error key=%s error=%s", key, str(e))
                raise
    
    def get_result(self, key: str) -> Optional[Any]:
        """Get result of previously processed operation"""
        with _tracer.start_as_current_span("get_result") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "idempotency")
            span.set_attribute("api.version", "v1")
            span.set_attribute("idempotency.key", key)
            
            try:
                result = self._idempotency_store.get(key)
                span.set_attribute("idempotency.result", "retrieved")
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("idempotency.result", "error")
                logger.error("event=idempotency_get_error key=%s error=%s", key, str(e))
                raise
    
    def clear_processed(self, key: str) -> bool:
        """Clear processed flag for a key"""
        with _tracer.start_as_current_span("clear_processed") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "idempotency")
            span.set_attribute("api.version", "v1")
            span.set_attribute("idempotency.key", key)
            
            try:
                result = self._idempotency_store.delete(key)
                span.set_attribute("idempotency.result", "cleared" if result else "not_found")
                logger.info("event=idempotency_clear key=%s success=%s", key, result)
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("idempotency.result", "error")
                logger.error("event=idempotency_clear_error key=%s error=%s", key, str(e))
                raise
    
    def cleanup_expired(self) -> int:
        """Clean up expired idempotency entries"""
        with _tracer.start_as_current_span("cleanup_expired") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "idempotency")
            span.set_attribute("api.version", "v1")
            
            try:
                count = self._idempotency_store.clear_expired()
                span.set_attribute("idempotency.result", "cleaned")
                span.set_attribute("idempotency.count", count)
                logger.info("event=idempotency_cleanup count=%d", count)
                return count
            except Exception as e:
                span.record_error(e)
                span.set_attribute("idempotency.result", "error")
                logger.error("event=idempotency_cleanup_error error=%s", str(e))
                raise
    
    def close(self):
        """Close the service"""
        self._idempotency_store.close()
