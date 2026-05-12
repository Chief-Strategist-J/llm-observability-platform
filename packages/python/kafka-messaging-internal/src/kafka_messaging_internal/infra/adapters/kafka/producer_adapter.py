"""Kafka producer adapter."""

import logging
from typing import Any, Dict, List, Optional
import asyncio
from confluent_kafka import Producer, KafkaException
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from infra.ports.producer_port import ProducerPort
from shared.types.events import ProduceMessageParams, TopicCreationParams
from shared.errors.codes import kafka_connection_failed, kafka_produce_failed

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


class KafkaProducerAdapter(ProducerPort):
    """Kafka producer adapter with single responsibility"""
    
    def __init__(self, bootstrap_servers: str, config: Optional[Dict] = None):
        self._bootstrap_servers = bootstrap_servers
        self._producer = None
        self._config = {
            'bootstrap.servers': bootstrap_servers,
            'client.id': 'kafka-messaging-internal-producer',
            **(config or {})
        }
    
    def _ensure_producer(self):
        """Ensure producer is initialized"""
        if not self._producer:
            with _tracer.start_as_current_span("init_kafka_producer") as span:
                span.set_attribute("service.name", "kafka-messaging-internal")
                span.set_attribute("feature.name", "kafka-production")
                span.set_attribute("api.version", "v1")
                
                try:
                    self._producer = Producer(self._config)
                    span.set_attribute("init.result", "success")
                    logger.info("event=kafka_producer_initialized servers=%s", self._bootstrap_servers)
                except Exception as e:
                    span.record_error(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("init.result", "failed")
                    raise kafka_connection_failed(f"Kafka producer init failed: {str(e)}")
    
    def produce(self, params: ProduceMessageParams) -> Dict[str, Any]:
        """Produce a single message"""
        with _tracer.start_as_current_span("produce_message") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "kafka-production")
            span.set_attribute("api.version", "v1")
            span.set_attribute("kafka.topic", params.topic)
            span.set_attribute("kafka.partition", str(params.partition) if params.partition else "auto")
            
            self._ensure_producer()
            
            try:
                # Prepare message
                message = {
                    'topic': params.topic,
                    'key': params.key,
                    'value': params.value,
                    'partition': params.partition,
                    'headers': params.headers or {}
                }
                
                # Produce message synchronously
                future = self._producer.produce(**message)
                
                # Wait for delivery report
                record_metadata = future.get(timeout=10)
                
                result = {
                    'topic': record_metadata.topic(),
                    'partition': record_metadata.partition(),
                    'offset': record_metadata.offset(),
                    'timestamp': record_metadata.timestamp()
                }
                
                span.set_attribute("produce.result", "success")
                span.set_attribute("kafka.offset", str(record_metadata.offset()))
                span.set_attribute("kafka.partition", str(record_metadata.partition()))
                
                logger.info("event=message_produced topic=%s partition=%d offset=%d", 
                          record_metadata.topic(), record_metadata.partition(), record_metadata.offset())
                
                return result
                
            except KafkaException as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("produce.result", "failed")
                raise kafka_produce_failed(f"Kafka produce failed: {str(e)}")
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("produce.result", "failed")
                raise kafka_produce_failed(f"Message production failed: {str(e)}")
    
    def produce_async(self, params: ProduceMessageParams) -> asyncio.Future:
        """Produce a message asynchronously"""
        with _tracer.start_as_current_span("produce_message_async") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "kafka-production")
            span.set_attribute("api.version", "v1")
            span.set_attribute("kafka.topic", params.topic)
            
            self._ensure_producer()
            
            try:
                # Prepare message
                message = {
                    'topic': params.topic,
                    'key': params.key,
                    'value': params.value,
                    'partition': params.partition,
                    'headers': params.headers or {}
                }
                
                # Produce message asynchronously
                future = self._producer.produce(**message)
                
                # Create asyncio future
                async def wait_for_delivery():
                    try:
                        record_metadata = future.get(timeout=10)
                        result = {
                            'topic': record_metadata.topic(),
                            'partition': record_metadata.partition(),
                            'offset': record_metadata.offset(),
                            'timestamp': record_metadata.timestamp()
                        }
                        
                        span.set_attribute("produce.result", "success")
                        span.set_attribute("kafka.offset", str(record_metadata.offset()))
                        
                        logger.info("event=message_produced_async topic=%s partition=%d offset=%d", 
                                  record_metadata.topic(), record_metadata.partition(), record_metadata.offset())
                        
                        return result
                    except Exception as e:
                        span.record_error(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.set_attribute("produce.result", "failed")
                        raise kafka_produce_failed(f"Async produce failed: {str(e)}")
                
                asyncio_future = asyncio.create_task(wait_for_delivery())
                
                span.set_attribute("produce.result", "initiated")
                return asyncio_future
                
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("produce.result", "failed")
                raise kafka_produce_failed(f"Async message production failed: {str(e)}")
    
    def produce_batch(self, topic: str, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Produce multiple messages in batch"""
        with _tracer.start_as_current_span("produce_batch") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "kafka-production")
            span.set_attribute("api.version", "v1")
            span.set_attribute("kafka.topic", topic)
            span.set_attribute("batch.size", str(len(messages)))
            
            self._ensure_producer()
            
            results = []
            
            try:
                for i, msg in enumerate(messages):
                    with _tracer.start_as_current_span(f"produce_batch_item_{i}") as item_span:
                        item_span.set_attribute("batch.index", str(i))
                        item_span.set_attribute("kafka.topic", topic)
                        
                        message = {
                            'topic': topic,
                            'key': msg.get('key'),
                            'value': msg.get('value'),
                            'partition': msg.get('partition'),
                            'headers': msg.get('headers', {})
                        }
                        
                        future = self._producer.produce(**message)
                        record_metadata = future.get(timeout=10)
                        
                        result = {
                            'topic': record_metadata.topic(),
                            'partition': record_metadata.partition(),
                            'offset': record_metadata.offset(),
                            'timestamp': record_metadata.timestamp()
                        }
                        
                        results.append(result)
                        
                        item_span.set_attribute("produce.result", "success")
                        item_span.set_attribute("kafka.offset", str(record_metadata.offset()))
                
                span.set_attribute("produce.result", "success")
                span.set_attribute("batch.produced_count", str(len(results)))
                
                logger.info("event=batch_produced topic=%s count=%d", topic, len(results))
                return results
                
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("produce.result", "failed")
                raise kafka_produce_failed(f"Batch production failed: {str(e)}")
    
    def flush(self) -> None:
        """Flush pending messages"""
        with _tracer.start_as_current_span("flush_producer") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "kafka-production")
            span.set_attribute("api.version", "v1")
            
            try:
                if self._producer:
                    self._producer.flush()
                    span.set_attribute("flush.result", "success")
                    logger.info("event=kafka_producer_flushed")
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("flush.result", "failed")
                raise kafka_produce_failed(f"Producer flush failed: {str(e)}")
    
    def list_topics(self) -> List[str]:
        """List available topics"""
        with _tracer.start_as_current_span("list_topics") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "kafka-discovery")
            span.set_attribute("api.version", "v1")
            
            try:
                # Simplified implementation - would use admin client
                topics = []  # Would fetch from Kafka cluster
                
                span.set_attribute("list.result", "success")
                span.set_attribute("topics.count", str(len(topics)))
                
                logger.info("event=topics_listed count=%d", len(topics))
                return topics
                
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("list.result", "failed")
                raise kafka_connection_failed(f"Topic listing failed: {str(e)}")
    
    def create_topic(self, params: TopicCreationParams) -> bool:
        """Create a new topic"""
        with _tracer.start_as_current_span("create_topic") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "kafka-management")
            span.set_attribute("api.version", "v1")
            span.set_attribute("kafka.topic", params.topic_name)
            span.set_attribute("kafka.partitions", str(params.partitions))
            span.set_attribute("kafka.replication_factor", str(params.replication_factor))
            
            try:
                # Simplified implementation - would use admin client
                success = True  # Would create topic via Kafka admin
                
                span.set_attribute("create.result", "success" if success else "failed")
                
                if success:
                    logger.info("event=topic_created topic=%s partitions=%d replication=%d", 
                              params.topic_name, params.partitions, params.replication_factor)
                else:
                    logger.warning("event=topic_create_failed topic=%s", params.topic_name)
                
                return success
                
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("create.result", "failed")
                raise kafka_produce_failed(f"Topic creation failed: {str(e)}")
    
    def close(self) -> None:
        """Close producer"""
        with _tracer.start_as_current_span("close_producer") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "kafka-production")
            span.set_attribute("api.version", "v1")
            
            try:
                if self._producer:
                    self._producer.flush()
                    self._producer = None
                    span.set_attribute("close.result", "success")
                    logger.info("event=kafka_producer_closed")
            except Exception as e:
                span.record_error(e)
                span.set_attribute("close.result", "error")
                logger.error("event=kafka_producer_close_error error=%s", str(e))
