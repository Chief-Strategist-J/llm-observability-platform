import asyncio
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from kafka import KafkaProducer as PyKafkaProducer
from kafka.errors import KafkaError
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.logql_logger import LogQLLogger
from infrastructure.orchestrator.kafka.utils.serializers import Serializer, StringSerializer
from infrastructure.orchestrator.kafka.utils.partition_selector import PartitionSelector, HashPartitioner
from infrastructure.orchestrator.kafka.utils.compression import CompressionType


@dataclass
class ProducerConfig:
    bootstrap_servers: List[str]
    client_id: str = "kafka-producer"
    acks: str = "all"
    retries: int = 3
    max_in_flight_requests: int = 5
    batch_size: int = 16384
    linger_ms: int = 0
    buffer_memory: int = 33554432
    compression_type: str = "none"
    enable_idempotence: bool = True
    transactional_id: Optional[str] = None
    request_timeout_ms: int = 30000
    retry_backoff_ms: int = 100
    max_block_ms: int = 60000
    key_serializer: Optional[Serializer] = None
    value_serializer: Optional[Serializer] = None
    partitioner: Optional[PartitionSelector] = None


@dataclass
class ProducerRecord:
    topic: str
    value: Any
    key: Optional[Any] = None
    partition: Optional[int] = None
    timestamp: Optional[int] = None
    headers: Optional[Dict[str, bytes]] = None


@dataclass
class RecordMetadata:
    topic: str
    partition: int
    offset: int
    timestamp: int
    serialized_key_size: int
    serialized_value_size: int


class KafkaProducerClient:
    __slots__ = ('_config', '_producer', '_logger', '_key_serializer', '_value_serializer', 
                 '_partitioner', '_closed', '_trace_id')
    
    def __init__(self, config: ProducerConfig):
        self._config = config
        self._logger = LogQLLogger(__name__)
        self._trace_id = self._logger.set_trace_id()
        
        self._key_serializer = config.key_serializer or StringSerializer()
        self._value_serializer = config.value_serializer or StringSerializer()
        self._partitioner = config.partitioner or HashPartitioner()
        self._closed = False
        
        self._logger.info(
            "producer_init_start",
            bootstrap_servers=','.join(config.bootstrap_servers),
            client_id=config.client_id,
            acks=config.acks,
            idempotence=config.enable_idempotence
        )
        
        try:
            producer_kwargs = {
                'bootstrap_servers': config.bootstrap_servers,
                'client_id': config.client_id,
                'acks': config.acks,
                'retries': config.retries,
                'max_in_flight_requests_per_connection': config.max_in_flight_requests,
                'batch_size': config.batch_size,
                'linger_ms': config.linger_ms,
                'buffer_memory': config.buffer_memory,
                'compression_type': config.compression_type,
                'enable_idempotence': config.enable_idempotence,
                'request_timeout_ms': config.request_timeout_ms,
                'retry_backoff_ms': config.retry_backoff_ms,
                'max_block_ms': config.max_block_ms,
            }
            
            if config.transactional_id:
                producer_kwargs['transactional_id'] = config.transactional_id
            
            self._producer = PyKafkaProducer(**producer_kwargs)
            
            self._logger.info(
                "producer_init_complete",
                bootstrap_servers=','.join(config.bootstrap_servers)
            )
            
        except Exception as e:
            self._logger.error("producer_init_failed", error=e)
            raise
    
    def send(
        self,
        record: ProducerRecord,
        callback: Optional[Callable[[RecordMetadata, Optional[Exception]], None]] = None
    ) -> 'ProducerFuture':
        if self._closed:
            raise RuntimeError("Producer is closed")
        
        start_time = time.time()
        
        try:
            key_bytes = self._key_serializer.serialize(record.key) if record.key is not None else None
            value_bytes = self._value_serializer.serialize(record.value)
            
            self._logger.debug(
                "producer_send",
                topic=record.topic,
                partition=record.partition,
                key_size=len(key_bytes) if key_bytes else 0,
                value_size=len(value_bytes)
            )
            
            future = self._producer.send(
                topic=record.topic,
                value=value_bytes,
                key=key_bytes,
                partition=record.partition,
                timestamp_ms=record.timestamp,
                headers=list(record.headers.items()) if record.headers else None
            )
            
            wrapped_future = ProducerFuture(future, self._logger)
            
            if callback:
                def on_complete(metadata, error):
                    duration_ms = int((time.time() - start_time) * 1000)
                    if error:
                        self._logger.error(
                            "producer_send_failed",
                            error=error,
                            topic=record.topic,
                            duration_ms=duration_ms
                        )
                    else:
                        self._logger.info(
                            "producer_send_complete",
                            topic=record.topic,
                            partition=metadata.partition,
                            offset=metadata.offset,
                            duration_ms=duration_ms
                        )
                    callback(metadata, error)
                
                wrapped_future.add_callback(on_complete)
            
            return wrapped_future
            
        except Exception as e:
            self._logger.error("producer_send_error", error=e, topic=record.topic)
            raise
    
    def flush(self, timeout: Optional[float] = None) -> None:
        if self._closed:
            return
        
        self._logger.debug("producer_flush_start")
        start_time = time.time()
        
        try:
            self._producer.flush(timeout=timeout)
            duration_ms = int((time.time() - start_time) * 1000)
            self._logger.info("producer_flush_complete", duration_ms=duration_ms)
        except Exception as e:
            self._logger.error("producer_flush_error", error=e)
            raise
    
    def close(self, timeout: Optional[float] = None) -> None:
        if self._closed:
            return
        
        self._logger.info("producer_close_start")
        
        try:
            self._producer.close(timeout=timeout)
            self._closed = True
            self._logger.info("producer_close_complete")
        except Exception as e:
            self._logger.error("producer_close_error", error=e)
            raise
    
    def partitions_for(self, topic: str) -> List[int]:
        try:
            partitions = self._producer.partitions_for(topic)
            return sorted(list(partitions)) if partitions else []
        except Exception as e:
            self._logger.error("producer_partitions_error", error=e, topic=topic)
            raise
    
    def metrics(self) -> Dict[str, Any]:
        try:
            return self._producer.metrics()
        except Exception as e:
            self._logger.error("producer_metrics_error", error=e)
            return {}


class ProducerFuture:
    def __init__(self, kafka_future, logger: LogQLLogger):
        self._future = kafka_future
        self._logger = logger
        self._callbacks = []
    
    def get(self, timeout: Optional[float] = None) -> RecordMetadata:
        try:
            record_metadata = self._future.get(timeout=timeout)
            metadata = RecordMetadata(
                topic=record_metadata.topic,
                partition=record_metadata.partition,
                offset=record_metadata.offset,
                timestamp=record_metadata.timestamp,
                serialized_key_size=record_metadata.serialized_key_size,
                serialized_value_size=record_metadata.serialized_value_size
            )
            
            for callback in self._callbacks:
                try:
                    callback(metadata, None)
                except Exception as e:
                    self._logger.error("producer_callback_error", error=e)
            
            return metadata
            
        except Exception as e:
            for callback in self._callbacks:
                try:
                    callback(None, e)
                except Exception as cb_error:
                    self._logger.error("producer_callback_error", error=cb_error)
            raise
    
    def add_callback(self, callback: Callable[[Optional[RecordMetadata], Optional[Exception]], None]) -> None:
        self._callbacks.append(callback)
        
        def on_success(record_metadata):
            metadata = RecordMetadata(
                topic=record_metadata.topic,
                partition=record_metadata.partition,
                offset=record_metadata.offset,
                timestamp=record_metadata.timestamp,
                serialized_key_size=record_metadata.serialized_key_size,
                serialized_value_size=record_metadata.serialized_value_size
            )
            callback(metadata, None)
        
        def on_error(error):
            callback(None, error)
        
        self._future.add_callback(on_success)
        self._future.add_errback(on_error)
