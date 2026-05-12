"""Database client with single responsibility."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from opentelemetry import trace

from shared.errors.codes import http_request_failed

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


class DatabaseClient:
    """Client for database operations with single responsibility"""
    
    def __init__(self, base_client):
        self._client = base_client
        self._base_path = "/api/v1/database"
    
    def save_event(self, topic: str, partition: int, offset: int, 
                   key: Optional[str] = None, value: Optional[Any] = None,
                   timestamp: Optional[datetime] = None, 
                   headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Save single event"""
        with _tracer.start_as_current_span("save_event") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "database-client")
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
                    "timestamp": timestamp.isoformat() if timestamp else None,
                    "headers": headers or {}
                }
                result = self._client.post(f"{self._base_path}/events", data=data)
                span.set_attribute("client.result", "success")
                span.set_attribute("event.id", result.get("event_id", ""))
                logger.info("event=event_saved topic=%s partition=%d offset=%d id=%s", topic, partition, offset, result.get("event_id", ""))
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=event_save_failed topic=%s partition=%d offset=%d error=%s", topic, partition, offset, str(e))
                raise http_request_failed(f"Failed to save event: {str(e)}")
    
    def save_events_batch(self, events: List[Dict]) -> Dict[str, Any]:
        """Save events in batch"""
        with _tracer.start_as_current_span("save_events_batch") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "database-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("events.count", str(len(events)))
            
            try:
                data = {"events": events}
                result = self._client.post(f"{self._base_path}/events/batch", data=data)
                span.set_attribute("client.result", "success")
                span.set_attribute("saved.count", str(len(result.get("saved_events", []))))
                logger.info("event=events_saved_batch count=%d saved=%d", len(events), len(result.get("saved_events", [])))
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=events_save_batch_failed count=%d error=%s", len(events), str(e))
                raise http_request_failed(f"Failed to save events batch: {str(e)}")
    
    def get_events(self, topic: Optional[str] = None, partition: Optional[int] = None,
                  limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get events"""
        with _tracer.start_as_current_span("get_events") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "database-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("limit", str(limit))
            span.set_attribute("offset", str(offset))
            
            if topic:
                span.set_attribute("topic.name", topic)
            if partition:
                span.set_attribute("partition", str(partition))
            
            try:
                params = {
                    "limit": limit,
                    "offset": offset
                }
                if topic:
                    params["topic"] = topic
                if partition:
                    params["partition"] = partition
                
                result = self._client.get(f"{self._base_path}/events", params=params)
                span.set_attribute("client.result", "success")
                span.set_attribute("events.count", str(len(result.get("events", []))))
                logger.info("event=events_retrieved count=%d", len(result.get("events", [])))
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=events_retrieve_failed error=%s", str(e))
                raise http_request_failed(f"Failed to get events: {str(e)}")
    
    def get_event(self, event_id: str) -> Dict[str, Any]:
        """Get specific event"""
        with _tracer.start_as_current_span("get_event") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "database-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("event.id", event_id)
            
            try:
                result = self._client.get(f"{self._base_path}/events/{event_id}")
                span.set_attribute("client.result", "success")
                logger.info("event=event_retrieved id=%s", event_id)
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=event_retrieve_failed id=%s error=%s", event_id, str(e))
                raise http_request_failed(f"Failed to get event: {str(e)}")
    
    def delete_event(self, event_id: str) -> Dict[str, bool]:
        """Delete event"""
        with _tracer.start_as_current_span("delete_event") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "database-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("event.id", event_id)
            
            try:
                result = self._client.delete(f"{self._base_path}/events/{event_id}")
                span.set_attribute("client.result", "success")
                logger.info("event=event_deleted id=%s", event_id)
                return {"success": True}
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=event_delete_failed id=%s error=%s", event_id, str(e))
                raise http_request_failed(f"Failed to delete event: {str(e)}")
    
    def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> Dict[str, Any]:
        """Get consumer offset"""
        with _tracer.start_as_current_span("get_consumer_offset") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "database-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("consumer.group", consumer_group)
            span.set_attribute("topic.name", topic)
            span.set_attribute("partition", str(partition))
            
            try:
                result = self._client.get(f"{self._base_path}/consumer-offsets/{consumer_group}/{topic}/{partition}")
                span.set_attribute("client.result", "success")
                logger.info("event=consumer_offset_retrieved group=%s topic=%s partition=%d", consumer_group, topic, partition)
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=consumer_offset_retrieve_failed group=%s topic=%s partition=%d error=%s", consumer_group, topic, partition, str(e))
                raise http_request_failed(f"Failed to get consumer offset: {str(e)}")
    
    def set_consumer_offset(self, consumer_group: str, topic: str, partition: int, offset: int) -> Dict[str, bool]:
        """Set consumer offset"""
        with _tracer.start_as_current_span("set_consumer_offset") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "database-client")
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
                result = self._client.post(f"{self._base_path}/consumer-offsets", data=data)
                span.set_attribute("client.result", "success")
                logger.info("event=consumer_offset_set group=%s topic=%s partition=%d offset=%d", consumer_group, topic, partition, offset)
                return {"success": True}
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=consumer_offset_set_failed group=%s topic=%s partition=%d error=%s", consumer_group, topic, partition, str(e))
                raise http_request_failed(f"Failed to set consumer offset: {str(e)}")
    
    def close(self):
        """Close client"""
        with _tracer.start_as_current_span("close_database_client") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "database-client")
            span.set_attribute("api.version", "v1")
            
            try:
                self._client.close()
                span.set_attribute("close.result", "success")
                logger.info("event=database_client_closed")
            except Exception as e:
                span.record_error(e)
                span.set_attribute("close.result", "failed")
                logger.error("event=database_client_close_error error=%s", str(e))
