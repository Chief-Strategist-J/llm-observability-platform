"""Event validation service."""

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ValidationError
from opentelemetry import trace

from shared.errors.codes import validation_failed
from shared.types.events import EventRecord

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


class EventValidator:
    """Service for validating events with single responsibility"""
    
    def __init__(self):
        self._required_fields = ["topic", "partition", "offset", "value"]
        self._max_value_size = 1024 * 1024  # 1MB max
    
    def validate_event_record(self, event_data: Dict[str, Any]) -> EventRecord:
        """Validate event record data"""
        with _tracer.start_as_current_span("validate_event_record") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "event-validation")
            span.set_attribute("api.version", "v1")
            
            try:
                # Check required fields
                missing_fields = [field for field in self._required_fields if field not in event_data]
                if missing_fields:
                    span.set_attribute("validation.result", "failed")
                    span.set_attribute("validation.reason", "missing_fields")
                    raise validation_failed(f"Missing required fields: {missing_fields}")
                
                # Validate field types and values
                self._validate_topic(event_data["topic"])
                self._validate_partition(event_data["partition"])
                self._validate_offset(event_data["offset"])
                self._validate_value(event_data["value"])
                
                # Optional fields
                key = event_data.get("key")
                if key is not None:
                    self._validate_key(key)
                
                headers = event_data.get("headers")
                if headers is not None:
                    self._validate_headers(headers)
                
                # Create EventRecord
                event = EventRecord(
                    topic=event_data["topic"],
                    partition=event_data["partition"],
                    offset=event_data["offset"],
                    key=key,
                    value=event_data["value"],
                    timestamp=event_data.get("timestamp"),
                    headers=headers,
                    event_id=event_data.get("event_id")
                )
                
                span.set_attribute("validation.result", "success")
                logger.info("event=validation_success topic=%s", event.topic)
                
                return event
                
            except Exception as e:
                span.record_error(e)
                span.set_attribute("validation.result", "failed")
                span.set_attribute("validation.error", str(e))
                logger.error("event=validation_failed error=%s", str(e))
                raise
    
    def _validate_topic(self, topic: Any) -> None:
        """Validate topic field"""
        if not isinstance(topic, str):
            raise validation_failed("Topic must be a string")
        
        if not topic.strip():
            raise validation_failed("Topic cannot be empty")
        
        if len(topic) > 255:
            raise validation_failed("Topic too long (max 255 characters)")
        
        # Basic topic naming rules
        if not re.match(r'^[a-zA-Z0-9._-]+$', topic):
            raise validation_failed("Topic contains invalid characters")
    
    def _validate_partition(self, partition: Any) -> None:
        """Validate partition field"""
        if not isinstance(partition, int):
            raise validation_failed("Partition must be an integer")
        
        if partition < 0:
            raise validation_failed("Partition must be non-negative")
        
        if partition > 1000:  # Reasonable limit
            raise validation_failed("Partition too large (max 1000)")
    
    def _validate_offset(self, offset: Any) -> None:
        """Validate offset field"""
        if not isinstance(offset, int):
            raise validation_failed("Offset must be an integer")
        
        if offset < 0:
            raise validation_failed("Offset must be non-negative")
    
    def _validate_value(self, value: Any) -> None:
        """Validate value field"""
        if value is None:
            raise validation_failed("Value cannot be None")
        
        # Check size if it's a string or bytes
        if isinstance(value, (str, bytes)):
            size = len(value)
            if size > self._max_value_size:
                raise validation_failed(f"Value too large (max {self._max_value_size} bytes)")
    
    def _validate_key(self, key: Any) -> None:
        """Validate key field"""
        if not isinstance(key, str):
            raise validation_failed("Key must be a string")
        
        if len(key) > 255:
            raise validation_failed("Key too long (max 255 characters)")
    
    def _validate_headers(self, headers: Any) -> None:
        """Validate headers field"""
        if not isinstance(headers, dict):
            raise validation_failed("Headers must be a dictionary")
        
        for key, value in headers.items():
            if not isinstance(key, str):
                raise validation_failed("Header keys must be strings")
            
            if len(key) > 255:
                raise validation_failed("Header key too long")
            
            # Check header value size
            if isinstance(value, (str, bytes)):
                if len(value) > 1024:  # 1KB per header
                    raise validation_failed("Header value too large")
