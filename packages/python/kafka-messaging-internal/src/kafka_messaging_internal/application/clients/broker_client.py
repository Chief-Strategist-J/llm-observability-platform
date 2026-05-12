"""Broker client with single responsibility."""

import logging
from typing import List, Dict, Any
from opentelemetry import trace

from shared.errors.codes import http_request_failed

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


class BrokerClient:
    """Client for broker operations with single responsibility"""
    
    def __init__(self, base_client):
        self._client = base_client
        self._base_path = "/api/v1/broker"
    
    def get_broker_metadata(self) -> Dict[str, Any]:
        """Get broker metadata"""
        with _tracer.start_as_current_span("get_broker_metadata") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "broker-client")
            span.set_attribute("api.version", "v1")
            
            try:
                result = self._client.get(f"{self._base_path}/metadata")
                span.set_attribute("client.result", "success")
                logger.info("event=broker_metadata_retrieved")
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=broker_metadata_failed error=%s", str(e))
                raise http_request_failed(f"Failed to get broker metadata: {str(e)}")
    
    def list_brokers(self) -> List[Dict[str, Any]]:
        """List all brokers"""
        with _tracer.start_as_current_span("list_brokers") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "broker-client")
            span.set_attribute("api.version", "v1")
            
            try:
                result = self._client.get(f"{self._base_path}/brokers")
                span.set_attribute("client.result", "success")
                span.set_attribute("brokers.count", str(len(result.get("brokers", []))))
                logger.info("event=brokers_listed count=%d", len(result.get("brokers", [])))
                return result.get("brokers", [])
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=brokers_list_failed error=%s", str(e))
                raise http_request_failed(f"Failed to list brokers: {str(e)}")
    
    def get_broker_info(self, broker_id: int) -> Dict[str, Any]:
        """Get specific broker info"""
        with _tracer.start_as_current_span("get_broker_info") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "broker-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("broker.id", str(broker_id))
            
            try:
                result = self._client.get(f"{self._base_path}/brokers/{broker_id}")
                span.set_attribute("client.result", "success")
                logger.info("event=broker_info_retrieved broker_id=%d", broker_id)
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=broker_info_failed broker_id=%d error=%s", broker_id, str(e))
                raise http_request_failed(f"Failed to get broker info: {str(e)}")
    
    def list_topics(self) -> Dict[str, List[str]]:
        """List all topics"""
        with _tracer.start_as_current_span("list_topics") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "broker-client")
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
    
    def get_topic_metadata(self, topic_name: str) -> Dict[str, Any]:
        """Get topic metadata"""
        with _tracer.start_as_current_span("get_topic_metadata") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "broker-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("topic.name", topic_name)
            
            try:
                result = self._client.get(f"{self._base_path}/topics/{topic_name}/metadata")
                span.set_attribute("client.result", "success")
                logger.info("event=topic_metadata_retrieved topic=%s", topic_name)
                return result
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=topic_metadata_failed topic=%s error=%s", topic_name, str(e))
                raise http_request_failed(f"Failed to get topic metadata: {str(e)}")
    
    def get_consumer_groups(self) -> List[Dict[str, Any]]:
        """Get consumer groups"""
        with _tracer.start_as_current_span("get_consumer_groups") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "broker-client")
            span.set_attribute("api.version", "v1")
            
            try:
                result = self._client.get(f"{self._base_path}/consumer-groups")
                groups = result.get("consumer_groups", [])
                span.set_attribute("client.result", "success")
                span.set_attribute("groups.count", str(len(groups)))
                logger.info("event=consumer_groups_retrieved count=%d", len(groups))
                return groups
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=consumer_groups_failed error=%s", str(e))
                raise http_request_failed(f"Failed to get consumer groups: {str(e)}")
    
    def get_consumer_group_lag(self, group_id: str) -> List[Dict[str, Any]]:
        """Get consumer group lag"""
        with _tracer.start_as_current_span("get_consumer_group_lag") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "broker-client")
            span.set_attribute("api.version", "v1")
            span.set_attribute("group.id", group_id)
            
            try:
                result = self._client.get(f"{self._base_path}/consumer-groups/{group_id}/lag")
                lag_info = result.get("lag", [])
                span.set_attribute("client.result", "success")
                span.set_attribute("lag.topics", str(len(lag_info)))
                logger.info("event=consumer_group_lag_retrieved group=%s topics=%d", group_id, len(lag_info))
                return lag_info
            except Exception as e:
                span.record_error(e)
                span.set_attribute("client.result", "failed")
                logger.error("event=consumer_group_lag_failed group=%s error=%s", group_id, str(e))
                raise http_request_failed(f"Failed to get consumer group lag: {str(e)}")
    
    def close(self):
        """Close client"""
        with _tracer.start_as_current_span("close_broker_client") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "broker-client")
            span.set_attribute("api.version", "v1")
            
            try:
                self._client.close()
                span.set_attribute("close.result", "success")
                logger.info("event=broker_client_closed")
            except Exception as e:
                span.record_error(e)
                span.set_attribute("close.result", "failed")
                logger.error("event=broker_client_close_error error=%s", str(e))
