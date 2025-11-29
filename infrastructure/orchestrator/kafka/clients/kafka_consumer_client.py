import time
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from kafka import KafkaConsumer as PyKafkaConsumer
from kafka.structs import TopicPartition, OffsetAndMetadata
from kafka.coordinator.assignors.range import RangePartitionAssignor
from kafka.coordinator.assignors.roundrobin import RoundRobinPartitionAssignor
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.logql_logger import LogQLLogger
from infrastructure.orchestrator.kafka.utils.serializers import Deserializer, StringDeserializer


@dataclass
class ConsumerConfig:
    bootstrap_servers: List[str]
    group_id: Optional[str] = None
    client_id: str = "kafka-consumer"
    enable_auto_commit: bool = True
    auto_commit_interval_ms: int = 5000
    auto_offset_reset: str = "latest"
    fetch_min_bytes: int = 1
    fetch_max_wait_ms: int = 500
    max_partition_fetch_bytes: int = 1048576
    session_timeout_ms: int = 10000
    heartbeat_interval_ms: int = 3000
    max_poll_records: int = 500
    max_poll_interval_ms: int = 300000
    isolation_level: str = "read_uncommitted"
    key_deserializer: Optional[Deserializer] = None
    value_deserializer: Optional[Deserializer] = None


@dataclass
class ConsumerRecord:
    topic: str
    partition: int
    offset: int
    timestamp: int
    key: Any
    value: Any
    headers: Optional[Dict[str, bytes]] = None
    checksum: Optional[int] = None
    serialized_key_size: int = 0
    serialized_value_size: int = 0


class KafkaConsumerClient:
    __slots__ = ('_config', '_consumer', '_logger', '_key_deserializer', '_value_deserializer',
                 '_closed', '_trace_id', '_subscribed_topics', '_assigned_partitions')
    
    def __init__(self, config: ConsumerConfig):
        self._config = config
        self._logger = LogQLLogger(__name__)
        self._trace_id = self._logger.set_trace_id()
        
        self._key_deserializer = config.key_deserializer or StringDeserializer()
        self._value_deserializer = config.value_deserializer or StringDeserializer()
        self._closed = False
        self._subscribed_topics: Set[str] = set()
        self._assigned_partitions: Set[TopicPartition] = set()
        
        self._logger.info(
            "consumer_init_start",
            bootstrap_servers=','.join(config.bootstrap_servers),
            client_id=config.client_id,
            group_id=config.group_id or "None"
        )
        
        try:
            consumer_kwargs = {
                'bootstrap_servers': config.bootstrap_servers,
                'client_id': config.client_id,
                'enable_auto_commit': config.enable_auto_commit,
                'auto_commit_interval_ms': config.auto_commit_interval_ms,
                'auto_offset_reset': config.auto_offset_reset,
                'fetch_min_bytes': config.fetch_min_bytes,
                'fetch_max_wait_ms': config.fetch_max_wait_ms,
                'max_partition_fetch_bytes': config.max_partition_fetch_bytes,
                'session_timeout_ms': config.session_timeout_ms,
                'heartbeat_interval_ms': config.heartbeat_interval_ms,
                'max_poll_records': config.max_poll_records,
                'max_poll_interval_ms': config.max_poll_interval_ms,
                'value_deserializer': lambda v: v,
                'key_deserializer': lambda k: k,
            }
            
            if config.group_id:
                consumer_kwargs['group_id'] = config.group_id
            
            self._consumer = PyKafkaConsumer(**consumer_kwargs)
            
            self._logger.info("consumer_init_complete")
            
        except Exception as e:
            self._logger.error("consumer_init_failed", error=e)
            raise
    
    def subscribe(self, topics: List[str], listener: Optional[Any] = None) -> None:
        if self._closed:
            raise RuntimeError("Consumer is closed")
        
        self._logger.info("consumer_subscribe", topics=','.join(topics))
        
        try:
            self._consumer.subscribe(topics=topics, listener=listener)
            self._subscribed_topics = set(topics)
            self._logger.info("consumer_subscribe_complete", topics=','.join(topics))
        except Exception as e:
            self._logger.error("consumer_subscribe_error", error=e, topics=','.join(topics))
            raise
    
    def assign(self, partitions: List[TopicPartition]) -> None:
        if self._closed:
            raise RuntimeError("Consumer is closed")
        
        self._logger.info(
            "consumer_assign",
            partitions_count=len(partitions)
        )
        
        try:
            self._consumer.assign(partitions)
            self._assigned_partitions = set(partitions)
            self._logger.info("consumer_assign_complete", partitions_count=len(partitions))
        except Exception as e:
            self._logger.error("consumer_assign_error", error=e)
            raise
    
    def poll(self, timeout_ms: int = 1000, max_records: Optional[int] = None) -> List[ConsumerRecord]:
        if self._closed:
            raise RuntimeError("Consumer is closed")
        
        start_time = time.time()
        
        try:
            records = self._consumer.poll(timeout_ms=timeout_ms, max_records=max_records or self._config.max_poll_records)
            
            consumer_records = []
            total_bytes = 0
            
            for topic_partition, messages in records.items():
                for message in messages:
                    key = self._key_deserializer.deserialize(message.key) if message.key else None
                    value = self._value_deserializer.deserialize(message.value)
                    
                    headers_dict = {}
                    if message.headers:
                        for header_key, header_value in message.headers:
                            headers_dict[header_key] = header_value
                    
                    record = ConsumerRecord(
                        topic=message.topic,
                        partition=message.partition,
                        offset=message.offset,
                        timestamp=message.timestamp,
                        key=key,
                        value=value,
                        headers=headers_dict if headers_dict else None,
                        checksum=message.checksum,
                        serialized_key_size=message.serialized_key_size,
                        serialized_value_size=message.serialized_value_size
                    )
                    
                    consumer_records.append(record)
                    total_bytes += message.serialized_value_size
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if consumer_records:
                self._logger.info(
                    "consumer_poll_complete",
                    records_count=len(consumer_records),
                    bytes_received=total_bytes,
                    duration_ms=duration_ms
                )
            else:
                self._logger.debug("consumer_poll_empty", duration_ms=duration_ms)
            
            return consumer_records
            
        except Exception as e:
            self._logger.error("consumer_poll_error", error=e)
            raise
    
    def commit(self, offsets: Optional[Dict[TopicPartition, OffsetAndMetadata]] = None) -> None:
        if self._closed:
            raise RuntimeError("Consumer is closed")
        
        self._logger.debug("consumer_commit_start")
        start_time = time.time()
        
        try:
            self._consumer.commit(offsets=offsets)
            duration_ms = int((time.time() - start_time) * 1000)
            self._logger.info("consumer_commit_complete", duration_ms=duration_ms)
        except Exception as e:
            self._logger.error("consumer_commit_error", error=e)
            raise
    
    def commit_async(self, offsets: Optional[Dict[TopicPartition, OffsetAndMetadata]] = None, 
                     callback: Optional[Any] = None) -> None:
        if self._closed:
            raise RuntimeError("Consumer is closed")
        
        self._logger.debug("consumer_commit_async")
        
        try:
            self._consumer.commit_async(offsets=offsets, callback=callback)
        except Exception as e:
            self._logger.error("consumer_commit_async_error", error=e)
            raise
    
    def seek(self, partition: TopicPartition, offset: int) -> None:
        if self._closed:
            raise RuntimeError("Consumer is closed")
        
        self._logger.info("consumer_seek", topic=partition.topic, partition=partition.partition, offset=offset)
        
        try:
            self._consumer.seek(partition, offset)
        except Exception as e:
            self._logger.error("consumer_seek_error", error=e)
            raise
    
    def seek_to_beginning(self, *partitions: TopicPartition) -> None:
        if self._closed:
            raise RuntimeError("Consumer is closed")
        
        self._logger.info("consumer_seek_to_beginning", partitions_count=len(partitions))
        
        try:
            self._consumer.seek_to_beginning(*partitions)
        except Exception as e:
            self._logger.error("consumer_seek_to_beginning_error", error=e)
            raise
    
    def seek_to_end(self, *partitions: TopicPartition) -> None:
        if self._closed:
            raise RuntimeError("Consumer is closed")
        
        self._logger.info("consumer_seek_to_end", partitions_count=len(partitions))
        
        try:
            self._consumer.seek_to_end(*partitions)
        except Exception as e:
            self._logger.error("consumer_seek_to_end_error", error=e)
            raise
    
    def position(self, partition: TopicPartition) -> int:
        try:
            return self._consumer.position(partition)
        except Exception as e:
            self._logger.error("consumer_position_error", error=e)
            raise
    
    def committed(self, partition: TopicPartition) -> Optional[OffsetAndMetadata]:
        try:
            return self._consumer.committed(partition)
        except Exception as e:
            self._logger.error("consumer_committed_error", error=e)
            raise
    
    def assignment(self) -> Set[TopicPartition]:
        return self._consumer.assignment()
    
    def subscription(self) -> Set[str]:
        return self._consumer.subscription()
    
    def pause(self, *partitions: TopicPartition) -> None:
        self._logger.info("consumer_pause", partitions_count=len(partitions))
        self._consumer.pause(*partitions)
    
    def resume(self, *partitions: TopicPartition) -> None:
        self._logger.info("consumer_resume", partitions_count=len(partitions))
        self._consumer.resume(*partitions)
    
    def close(self, autocommit: bool = True) -> None:
        if self._closed:
            return
        
        self._logger.info("consumer_close_start", autocommit=autocommit)
        
        try:
            self._consumer.close(autocommit=autocommit)
            self._closed = True
            self._logger.info("consumer_close_complete")
        except Exception as e:
            self._logger.error("consumer_close_error", error=e)
            raise
    
    def metrics(self) -> Dict[str, Any]:
        try:
            return self._consumer.metrics()
        except Exception as e:
            self._logger.error("consumer_metrics_error", error=e)
            return {}
