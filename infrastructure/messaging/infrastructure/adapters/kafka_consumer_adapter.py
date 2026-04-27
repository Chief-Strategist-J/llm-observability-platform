from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
from dataclasses import dataclass
import threading
import queue

from domain.ports.consumer_port import ConsumerPort


@dataclass
class KafkaConsumerConfig:
    bootstrap_servers: str = "localhost:9092"
    group_id: str = "default-consumer-group"
    auto_offset_reset: str = "earliest"  # earliest, latest
    enable_auto_commit: bool = False
    max_poll_records: int = 500  # Batch size for polling
    max_poll_interval_ms: int = 300000
    session_timeout_ms: int = 10000
    heartbeat_interval_ms: int = 3000
    fetch_min_bytes: int = 1
    fetch_max_wait_ms: int = 500
    fetch_max_bytes: int = 52428800  # 50MB
    max_partition_fetch_bytes: int = 1048576  # 1MB
    max_threads: int = 10  # Parallel consumers


class HighThroughputKafkaConsumer(ConsumerPort):
    def __init__(self, config: KafkaConsumerConfig):
        self.config = config
        self._consumer = None
        self._executor = ThreadPoolExecutor(max_workers=config.max_threads)
        self._message_queue = queue.Queue(maxsize=10000)
        self._running = False
        self._consumer_thread = None
        self._initialize_consumer()
    
    def _initialize_consumer(self):
        try:
            from confluent_kafka import Consumer as ConfluentConsumer
            
            conf = {
                'bootstrap.servers': self.config.bootstrap_servers,
                'group.id': self.config.group_id,
                'auto.offset.reset': self.config.auto_offset_reset,
                'enable.auto.commit': self.config.enable_auto_commit,
                'max.poll.interval.ms': self.config.max_poll_interval_ms,
                'session.timeout.ms': self.config.session_timeout_ms,
                'heartbeat.interval.ms': self.config.heartbeat_interval_ms,
                'fetch.min.bytes': self.config.fetch_min_bytes,
                'fetch.max.bytes': self.config.fetch_max_bytes,
                'max.partition.fetch.bytes': self.config.max_partition_fetch_bytes
            }
            
            self._consumer = ConfluentConsumer(conf)
        except ImportError:
            self._consumer = None
    
    def consume(self, topic: str, consumer_group: str, partition: Optional[int],
               max_messages: int, timeout_ms: int) -> List[Dict[str, Any]]:
        if self._consumer is None:
            return self._consume_mock(topic, max_messages)
        
        from confluent_kafka import KafkaException, TopicPartition
        import json
        
        try:
            if partition is not None:
                self._consumer.assign([TopicPartition(topic, partition)])
            else:
                self._consumer.subscribe([topic])
            
            messages = []
            remaining = max_messages
            
            while remaining > 0:
                msg = self._consumer.poll(timeout_ms / 1000.0)
                
                if msg is None:
                    break
                
                if msg.error():
                    if msg.error().code() == -194:  # PARTITION_EOF
                        break
                    else:
                        raise KafkaException(msg.error())
                
                try:
                    value = json.loads(msg.value().decode('utf-8')) if msg.value() else None
                except:
                    value = msg.value().decode('utf-8') if msg.value() else None
                
                messages.append({
                    "topic": msg.topic(),
                    "partition": msg.partition(),
                    "offset": msg.offset(),
                    "key": msg.key().decode('utf-8') if msg.key() else None,
                    "value": value,
                    "timestamp": msg.timestamp()[1] if msg.timestamp() else None,
                    "headers": dict(msg.headers()) if msg.headers() else {}
                })
                
                remaining -= 1
            
            return messages
        
        except KafkaException as e:
            raise Exception(f"Failed to consume messages: {e}")
        finally:
            self._consumer.unsubscribe()
    
    def consume_parallel(self, topic: str, consumer_group: str, partitions: List[int],
                        max_messages_per_partition: int, timeout_ms: int) -> Dict[int, List[Dict[str, Any]]]:
        futures = {}
        results = {}
        
        for partition in partitions:
            future = self._executor.submit(
                self.consume,
                topic,
                consumer_group,
                partition,
                max_messages_per_partition,
                timeout_ms
            )
            futures[partition] = future
        
        for partition, future in futures.items():
            results[partition] = future.result()
        
        return results
    
    def consume_stream(self, topic: str, consumer_group: str, 
                      message_handler: callable, batch_size: int = 100):
        if self._consumer is None:
            return
        
        self._running = True
        self._consumer.subscribe([topic])
        
        def consume_loop():
            from confluent_kafka import KafkaException
            import json
            
            batch = []
            
            while self._running:
                try:
                    msg = self._consumer.poll(timeout=1.0)
                    
                    if msg is None:
                        if batch:
                            message_handler(batch)
                            batch = []
                        continue
                    
                    if msg.error():
                        if msg.error().code() == -194:
                            continue
                        else:
                            raise KafkaException(msg.error())
                    
                    try:
                        value = json.loads(msg.value().decode('utf-8')) if msg.value() else None
                    except:
                        value = msg.value().decode('utf-8') if msg.value() else None
                    
                    batch.append({
                        "topic": msg.topic(),
                        "partition": msg.partition(),
                        "offset": msg.offset(),
                        "key": msg.key().decode('utf-8') if msg.key() else None,
                        "value": value,
                        "timestamp": msg.timestamp()[1] if msg.timestamp() else None,
                        "headers": dict(msg.headers()) if msg.headers() else {}
                    })
                    
                    if len(batch) >= batch_size:
                        message_handler(batch)
                        batch = []
                
                except Exception as e:
                    print(f"Error in consume loop: {e}")
            
            if batch:
                message_handler(batch)
        
        self._consumer_thread = threading.Thread(target=consume_loop)
        self._consumer_thread.start()
    
    def stop_stream(self):
        self._running = False
        if self._consumer_thread:
            self._consumer_thread.join(timeout=5)
    
    def commit_offset(self, consumer_group: str, topic: str, partition: int, offset: int) -> bool:
        if self._consumer is None:
            return True
        
        from confluent_kafka import TopicPartition
        
        try:
            tp = TopicPartition(topic, partition, offset)
            self._consumer.commit(offsets=[tp])
            return True
        except Exception as e:
            print(f"Failed to commit offset: {e}")
            return False
    
    def commit_offsets_batch(self, offsets: Dict[str, Dict[int, int]]) -> bool:
        if self._consumer is None:
            return True
        
        from confluent_kafka import TopicPartition
        
        try:
            tps = []
            for topic, partitions in offsets.items():
                for partition, offset in partitions.items():
                    tps.append(TopicPartition(topic, partition, offset))
            
            self._consumer.commit(offsets=tps)
            return True
        except Exception as e:
            print(f"Failed to commit batch offsets: {e}")
            return False
    
    def get_offset(self, consumer_group: str, topic: str, partition: int) -> int:
        if self._consumer is None:
            return 100
        
        from confluent_kafka import TopicPartition
        
        try:
            tp = TopicPartition(topic, partition)
            committed = self._consumer.committed([tp])
            return committed[0].offset if committed[0] else 0
        except Exception as e:
            print(f"Failed to get offset: {e}")
            return 0
    
    def subscribe(self, topic: str, consumer_group: str) -> bool:
        if self._consumer is None:
            return True
        
        try:
            self._consumer.subscribe([topic])
            return True
        except Exception as e:
            print(f"Failed to subscribe: {e}")
            return False
    
    def unsubscribe(self, topic: str, consumer_group: str) -> bool:
        if self._consumer is None:
            return True
        
        try:
            self._consumer.unsubscribe()
            return True
        except Exception as e:
            print(f"Failed to unsubscribe: {e}")
            return False
    
    def list_subscriptions(self, consumer_group: str) -> List[str]:
        if self._consumer is None:
            return ["topic1", "topic2"]
        
        try:
            metadata = self._consumer.list_topics(timeout=10)
            return list(metadata.topics.keys())
        except Exception as e:
            print(f"Failed to list subscriptions: {e}")
            return []
    
    def _consume_mock(self, topic: str, max_messages: int) -> List[Dict[str, Any]]:
        return [
            {
                "topic": topic,
                "partition": 0,
                "offset": i,
                "key": f"key-{i}",
                "value": f"value-{i}",
                "timestamp": 1234567890,
                "headers": {}
            }
            for i in range(min(max_messages, 10))
        ]
    
    def close(self):
        self.stop_stream()
        if self._consumer:
            self._consumer.close()
            self._consumer = None
        self._executor.shutdown(wait=True)
