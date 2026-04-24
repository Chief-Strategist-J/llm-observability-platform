from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
import asyncio
from dataclasses import dataclass

from infrastructure.messaging.domain.ports.producer_port import ProducerPort


@dataclass
class KafkaProducerConfig:
    bootstrap_servers: str = "localhost:9092"
    batch_size: int = 65536  # 64KB (can go up to 128KB)
    linger_ms: int = 10  # Wait up to 10ms to batch messages
    compression_type: str = "snappy"  # snappy, lz4, gzip, none
    acks: str = "all"  # 0=fire&forget, 1=leader ack, all=all replicas
    max_in_flight_requests_per_connection: int = 5
    retries: int = 3
    enable_idempotence: bool = True
    max_request_size: int = 1048576  # 1MB


class HighThroughputKafkaProducer(ProducerPort):
    def __init__(self, config: KafkaProducerConfig):
        self.config = config
        self._producer = None
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._initialize_producer()
    
    def _initialize_producer(self):
        try:
            from confluent_kafka import Producer as ConfluentProducer
            
            conf = {
                'bootstrap.servers': self.config.bootstrap_servers,
                'batch.size': self.config.batch_size,
                'linger.ms': self.config.linger_ms,
                'compression.type': self.config.compression_type,
                'acks': self.config.acks,
                'max.in.flight.requests.per.connection': self.config.max_in_flight_requests_per_connection,
                'retries': self.config.retries,
                'enable.idempotence': self.config.enable_idempotence,
                'message.max.bytes': self.config.max_request_size
            }
            
            self._producer = ConfluentProducer(conf)
        except ImportError:
            self._producer = None
    
    def produce(self, topic: str, key: Optional[str], value: Any, 
               partition: Optional[int], headers: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if self._producer is None:
            return self._produce_mock(topic, key, value, partition, headers)
        
        import json
        from confluent_kafka import KafkaException
        
        try:
            message_value = json.dumps(value) if not isinstance(value, (str, bytes)) else value
            message_key = str(key) if key is not None else None
            
            def delivery_report(err, msg):
                if err is not None:
                    print(f"Message delivery failed: {err}")
            
            self._producer.produce(
                topic=topic,
                key=message_key,
                value=message_value,
                partition=partition,
                headers=headers,
                callback=delivery_report
            )
            
            self._producer.poll(0)  # Trigger delivery reports
            
            return {
                "topic": topic,
                "partition": partition or 0,
                "offset": -1,  # Async, offset not immediately available
                "status": "queued"
            }
        except KafkaException as e:
            raise Exception(f"Failed to produce message: {e}")
    
    def produce_batch(self, topic: str, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for msg in messages:
            result = self.produce(
                topic=topic,
                key=msg.get("key"),
                value=msg.get("value"),
                partition=msg.get("partition"),
                headers=msg.get("headers")
            )
            results.append(result)
        
        if self._producer:
            self._producer.flush(timeout=10)
        return results
    
    def produce_async(self, topic: str, key: Optional[str], value: Any,
                     partition: Optional[int], headers: Optional[Dict[str, Any]]) -> asyncio.Future:
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        
        def callback(err, msg):
            if err is not None:
                loop.call_soon_threadsafe(future.set_exception, Exception(str(err)))
            else:
                result = {
                    "topic": msg.topic(),
                    "partition": msg.partition(),
                    "offset": msg.offset(),
                    "status": "delivered"
                }
                loop.call_soon_threadsafe(future.set_result, result)
        
        self._producer.produce(
            topic=topic,
            key=str(key) if key else None,
            value=str(value) if isinstance(value, (str, int, float)) else str(value),
            partition=partition,
            headers=headers,
            callback=callback
        )
        
        return future
    
    def list_topics(self) -> List[str]:
        if self._producer is None:
            return ["topic1", "topic2"]
        
        cluster_metadata = self._producer.list_topics(timeout=10)
        return list(cluster_metadata.topics.keys())
    
    def create_topic(self, topic_name: str, partitions: int, replication_factor: int) -> bool:
        try:
            from confluent_kafka.admin import AdminClient, NewTopic
        except ImportError:
            return True
        
        try:
            admin_client = AdminClient({'bootstrap.servers': self.config.bootstrap_servers})
            
            new_topic = NewTopic(
                topic_name,
                num_partitions=partitions,
                replication_factor=replication_factor
            )
            
            futures = admin_client.create_topics([new_topic])
            
            for topic, future in futures.items():
                try:
                    future.result()
                    return True
                except Exception as e:
                    print(f"Failed to create topic: {e}")
                    return False
        except Exception as e:
            print(f"Failed to create topic: {e}")
            return True
    
    def flush(self, timeout: float = 10.0):
        if self._producer:
            self._producer.flush(timeout=timeout)
    
    def _produce_mock(self, topic: str, key: Optional[str], value: Any,
                     partition: Optional[int], headers: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "topic": topic,
            "partition": partition or 0,
            "offset": 100,
            "status": "mock"
        }
    
    def close(self):
        if self._producer:
            self._producer.flush(timeout=10)
            self._producer = None
        self._executor.shutdown(wait=True)
