"""Kafka consumer adapter."""

import logging
from typing import Any, Dict, List, Optional
import asyncio
from confluent_kafka import Consumer, KafkaException, TopicPartition
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from infra.ports.consumer_port import ConsumerPort
from shared.types.events import ConsumeParams, ParallelConsumeParams, ConsumerOffsetParams
from shared.errors.codes import kafka_connection_failed

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


class KafkaConsumerAdapter(ConsumerPort):
    """Kafka consumer adapter with single responsibility"""
    
    def __init__(self, bootstrap_servers: str, config: Optional[Dict] = None):
        self._bootstrap_servers = bootstrap_servers
        self._consumer = None
        self._config = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': 'kafka-messaging-internal-consumer',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False,
            **(config or {})
        }
    
    def _ensure_consumer(self):
        """Ensure consumer is initialized"""
        if not self._consumer:
            with _tracer.start_as_current_span("init_kafka_consumer") as span:
                span.set_attribute("service.name", "kafka-messaging-internal")
                span.set_attribute("feature.name", "kafka-consumption")
                span.set_attribute("api.version", "v1")
                
                try:
                    self._consumer = Consumer(self._config)
                    span.set_attribute("init.result", "success")
                    logger.info("event=kafka_consumer_initialized servers=%s", self._bootstrap_servers)
                except Exception as e:
                    span.record_error(e)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("init.result", "failed")
                    raise kafka_connection_failed(f"Kafka consumer init failed: {str(e)}")
    
    def consume(self, params: ConsumeParams) -> List[Dict[str, Any]]:
        """Consume messages from topic"""
        with _tracer.start_as_current_span("consume_messages") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "kafka-consumption")
            span.set_attribute("api.version", "v1")
            span.set_attribute("kafka.topic", params.topic)
            span.set_attribute("kafka.partition", str(params.partition) if params.partition else "all")
            
            self._ensure_consumer()
            
            try:
                # Subscribe to topic
                self._consumer.subscribe([params.topic])
                
                # Poll for messages
                messages = []
                timeout_ms = params.timeout * 1000 if params.timeout else 10000
                
                while len(messages) < params.max_messages:
                    msg = self._consumer.poll(timeout=1.0)
                    
                    if msg is None:
                        break
                    
                    if msg.error():
                        logger.warning("kafka_message_error error=%s", msg.error())
                        continue
                    
                    message_data = {
                        'topic': msg.topic(),
                        'partition': msg.partition(),
                        'offset': msg.offset(),
                        'key': msg.key(),
                        'value': msg.value(),
                        'timestamp': msg.timestamp(),
                        'headers': dict(msg.headers())
                    }
                    
                    messages.append(message_data)
                    
                    if len(messages) >= params.max_messages:
                        break
                
                span.set_attribute("consume.result", "success")
                span.set_attribute("messages.count", len(messages))
                
                logger.info("event=messages_consumed topic=%s count=%d", params.topic, len(messages))
                return messages
                
            except KafkaException as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("consume.result", "failed")
                raise kafka_connection_failed(f"Kafka consume failed: {str(e)}")
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("consume.result", "failed")
                raise
    
    def consume_parallel(self, params: ParallelConsumeParams) -> Dict[int, List[Dict[str, Any]]]:
        """Consume messages from multiple partitions in parallel"""
        with _tracer.start_as_current_span("consume_parallel") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "kafka-consumption")
            span.set_attribute("api.version", "v1")
            span.set_attribute("kafka.topic", params.topic)
            span.set_attribute("partitions.count", len(params.partitions))
            
            self._ensure_consumer()
            
            try:
                # Assign specific partitions
                partitions = [TopicPartition(params.topic, p) for p in params.partitions]
                self._consumer.assign(partitions)
                
                results = {}
                timeout_ms = params.timeout * 1000 if params.timeout else 10000
                
                for partition in params.partitions:
                    results[partition] = []
                
                messages_collected = 0
                
                while messages_collected < params.max_messages:
                    msg = self._consumer.poll(timeout=1.0)
                    
                    if msg is None:
                        break
                    
                    if msg.error():
                        logger.warning("kafka_message_error error=%s", msg.error())
                        continue
                    
                    partition = msg.partition()
                    if partition not in results:
                        results[partition] = []
                    
                    message_data = {
                        'topic': msg.topic(),
                        'partition': msg.partition(),
                        'offset': msg.offset(),
                        'key': msg.key(),
                        'value': msg.value(),
                        'timestamp': msg.timestamp(),
                        'headers': dict(msg.headers())
                    }
                    
                    results[partition].append(message_data)
                    messages_collected += 1
                    
                    if messages_collected >= params.max_messages:
                        break
                
                span.set_attribute("consume.result", "success")
                span.set_attribute("messages.count", messages_collected)
                
                logger.info("event=messages_consumed_parallel topic=%s count=%d", params.topic, messages_collected)
                return results
                
            except KafkaException as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("consume.result", "failed")
                raise kafka_connection_failed(f"Kafka parallel consume failed: {str(e)}")
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("consume.result", "failed")
                raise
    
    def consume_stream(self, params: ConsumeParams):
        """Consume messages as a stream"""
        with _tracer.start_as_current_span("consume_stream") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "kafka-consumption")
            span.set_attribute("api.version", "v1")
            span.set_attribute("kafka.topic", params.topic)
            
            self._ensure_consumer()
            
            try:
                # Subscribe to topic
                self._consumer.subscribe([params.topic])
                
                def message_generator():
                    timeout_ms = params.timeout * 1000 if params.timeout else 10000
                    messages_yielded = 0
                    
                    while messages_yielded < params.max_messages:
                        msg = self._consumer.poll(timeout=1.0)
                        
                        if msg is None:
                            break
                        
                        if msg.error():
                            logger.warning("kafka_message_error error=%s", msg.error())
                            continue
                        
                        message_data = {
                            'topic': msg.topic(),
                            'partition': msg.partition(),
                            'offset': msg.offset(),
                            'key': msg.key(),
                            'value': msg.value(),
                            'timestamp': msg.timestamp(),
                            'headers': dict(msg.headers())
                        }
                        
                        yield message_data
                        messages_yielded += 1
                        
                        if messages_yielded >= params.max_messages:
                            break
                
                span.set_attribute("consume.result", "success")
                return message_generator()
                
            except KafkaException as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("consume.result", "failed")
                raise kafka_connection_failed(f"Kafka stream consume failed: {str(e)}")
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("consume.result", "failed")
                raise
    
    def commit(self) -> None:
        """Commit current offsets"""
        with _tracer.start_as_current_span("commit_offsets") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "kafka-consumption")
            span.set_attribute("api.version", "v1")
            
            try:
                if self._consumer:
                    self._consumer.commit()
                    span.set_attribute("commit.result", "success")
                    logger.info("event=kafka_offsets_committed")
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("commit.result", "failed")
                raise kafka_connection_failed(f"Kafka commit failed: {str(e)}")
    
    def commit_offset(self, params: ConsumerOffsetParams) -> None:
        """Commit specific offset"""
        with _tracer.start_as_current_span("commit_offset") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "kafka-consumption")
            span.set_attribute("api.version", "v1")
            span.set_attribute("kafka.topic", params.topic)
            span.set_attribute("kafka.partition", str(params.partition))
            span.set_attribute("kafka.offset", str(params.offset))
            
            try:
                if self._consumer:
                    partition = TopicPartition(params.topic, params.partition, params.offset)
                    self._consumer.commit(offsets=[partition])
                    span.set_attribute("commit.result", "success")
                    logger.info("event=kafka_offset_committed topic=%s partition=%d offset=%d", 
                              params.topic, params.partition, params.offset)
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("commit.result", "failed")
                raise kafka_connection_failed(f"Kafka offset commit failed: {str(e)}")
    
    def subscribe(self, topics: List[str]) -> None:
        """Subscribe to topics"""
        with _tracer.start_as_current_span("subscribe_topics") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "kafka-consumption")
            span.set_attribute("api.version", "v1")
            span.set_attribute("topics.count", len(topics))
            
            try:
                if self._consumer:
                    self._consumer.subscribe(topics)
                    span.set_attribute("subscribe.result", "success")
                    logger.info("event=kafka_subscribed topics=%s", topics)
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("subscribe.result", "failed")
                raise kafka_connection_failed(f"Kafka subscribe failed: {str(e)}")
    
    def unsubscribe(self) -> None:
        """Unsubscribe from all topics"""
        with _tracer.start_as_current_span("unsubscribe_topics") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "kafka-consumption")
            span.set_attribute("api.version", "v1")
            
            try:
                if self._consumer:
                    self._consumer.unsubscribe()
                    span.set_attribute("unsubscribe.result", "success")
                    logger.info("event=kafka_unsubscribed")
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("unsubscribe.result", "failed")
                raise kafka_connection_failed(f"Kafka unsubscribe failed: {str(e)}")
    
    def get_committed_offsets(self, topic: str, partitions: List[int]) -> Dict[int, int]:
        """Get committed offsets"""
        with _tracer.start_as_current_span("get_committed_offsets") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "kafka-consumption")
            span.set_attribute("api.version", "v1")
            span.set_attribute("kafka.topic", topic)
            span.set_attribute("partitions.count", len(partitions))
            
            try:
                if self._consumer:
                    partitions_list = [TopicPartition(topic, p) for p in partitions]
                    committed = self._consumer.committed(partitions_list)
                    
                    result = {}
                    for tp, offset in zip(partitions_list, committed):
                        if offset is not None:
                            result[tp.partition] = offset
                    
                    span.set_attribute("get_offsets.result", "success")
                    span.set_attribute("offsets.count", len(result))
                    
                    logger.info("event=kafka_offsets_retrieved topic=%s count=%d", topic, len(result))
                    return result
                else:
                    span.set_attribute("get_offsets.result", "no_consumer")
                    return {}
                    
            except Exception as e:
                span.record_error(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("get_offsets.result", "failed")
                raise kafka_connection_failed(f"Kafka get committed offsets failed: {str(e)}")
    
    def close(self) -> None:
        """Close consumer"""
        with _tracer.start_as_current_span("close_consumer") as span:
            span.set_attribute("service.name", "kafka-messaging-internal")
            span.set_attribute("feature.name", "kafka-consumption")
            span.set_attribute("api.version", "v1")
            
            try:
                if self._consumer:
                    self._consumer.close()
                    self._consumer = None
                    span.set_attribute("close.result", "success")
                    logger.info("event=kafka_consumer_closed")
            except Exception as e:
                span.record_error(e)
                span.set_attribute("close.result", "failed")
                logger.error("event=kafka_consumer_close_error error=%s", str(e))
