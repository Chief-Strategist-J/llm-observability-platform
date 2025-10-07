#!/usr/bin/env python3
"""
Comprehensive Kafka Testing Script
Tests producer, consumer, and various Kafka features
"""

import json
import time
from datetime import datetime
from typing import Dict, Any
from kafka import KafkaProducer, KafkaConsumer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import KafkaError, TopicAlreadyExistsError


# Default bootstrap servers - external listener exposed by Docker
DEFAULT_BOOTSTRAP_SERVERS = 'localhost:29092'

# Alternative: use container name for Docker network (if needed)
# DEFAULT_BOOTSTRAP_SERVERS = 'kafka:9092'


class KafkaTestSuite:
    def __init__(self, bootstrap_servers=None):
        self.bootstrap_servers = bootstrap_servers or DEFAULT_BOOTSTRAP_SERVERS
        self.test_topic = 'test-topic'
        self.results = []
        
    def log(self, message: str, status: str = "INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] [{status}] {message}"
        print(log_msg)
        self.results.append({"time": timestamp, "status": status, "message": message})
        
    def test_connection(self) -> bool:
        """Test basic Kafka connection"""
        self.log("Testing Kafka connection...")
        try:
            admin = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                request_timeout_ms=5000
            )
            cluster_metadata = admin.list_topics()
            self.log(f"Connected successfully! Found {len(cluster_metadata)} topics", "SUCCESS")
            admin.close()
            return True
        except Exception as e:
            self.log(f"Connection failed: {str(e)}", "ERROR")
            return False
    
    def create_topic(self) -> bool:
        """Create test topic"""
        self.log(f"Creating topic: {self.test_topic}")
        try:
            admin = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
            topic = NewTopic(
                name=self.test_topic,
                num_partitions=3,
                replication_factor=1
            )
            admin.create_topics([topic])
            self.log(f"Topic '{self.test_topic}' created successfully", "SUCCESS")
            admin.close()
            return True
        except TopicAlreadyExistsError:
            self.log(f"Topic '{self.test_topic}' already exists", "INFO")
            return True
        except Exception as e:
            self.log(f"Failed to create topic: {str(e)}", "ERROR")
            return False
    
    def test_producer(self, num_messages: int = 10) -> bool:
        """Test message production"""
        self.log(f"Testing producer - sending {num_messages} messages...")
        try:
            producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                max_request_size=10485760,  # 10MB
                acks='all',
                retries=3
            )
            
            success_count = 0
            for i in range(num_messages):
                message = {
                    'id': i,
                    'timestamp': datetime.now().isoformat(),
                    'message': f'Test message {i}',
                    'data': f'Sample data for message {i}'
                }
                
                future = producer.send(self.test_topic, value=message)
                try:
                    record_metadata = future.get(timeout=10)
                    success_count += 1
                    if i == 0 or i == num_messages - 1:
                        self.log(
                            f"Message {i} sent to partition {record_metadata.partition} "
                            f"at offset {record_metadata.offset}",
                            "SUCCESS"
                        )
                except Exception as e:
                    self.log(f"Failed to send message {i}: {str(e)}", "ERROR")
                
            producer.flush()
            producer.close()
            
            self.log(f"Producer test complete: {success_count}/{num_messages} messages sent", "SUCCESS")
            return success_count == num_messages
            
        except Exception as e:
            self.log(f"Producer test failed: {str(e)}", "ERROR")
            return False
    
    def test_consumer(self, timeout: int = 30) -> bool:
        """Test message consumption"""
        self.log(f"Testing consumer - reading messages (timeout: {timeout}s)...")
        try:
            consumer = KafkaConsumer(
                self.test_topic,
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='test-group',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                consumer_timeout_ms=timeout * 1000,
                max_partition_fetch_bytes=10485760  # 10MB
            )
            
            message_count = 0
            start_time = time.time()
            
            for message in consumer:
                message_count += 1
                if message_count <= 3 or message_count % 5 == 0:
                    self.log(
                        f"Received message {message_count} from partition {message.partition} "
                        f"at offset {message.offset}",
                        "SUCCESS"
                    )
                
                # Break if we've been running too long
                if time.time() - start_time > timeout:
                    break
            
            consumer.close()
            
            if message_count > 0:
                self.log(f"Consumer test complete: {message_count} messages received", "SUCCESS")
                return True
            else:
                self.log("No messages received", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Consumer test failed: {str(e)}", "ERROR")
            return False
    
    def test_large_message(self, size_mb: float = 5.0) -> bool:
        """Test sending and receiving a large message"""
        self.log(f"Testing large message ({size_mb}MB)...")
        try:
            producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                max_request_size=10485760,
                acks='all'
            )
            
            # Create a large message (approximately size_mb MB)
            large_data = 'x' * int(size_mb * 1024 * 1024)
            message = {
                'id': 'large-message-test',
                'timestamp': datetime.now().isoformat(),
                'size_mb': size_mb,
                'data': large_data
            }
            
            future = producer.send(self.test_topic, value=message)
            record_metadata = future.get(timeout=15)
            producer.close()
            
            self.log(f"Large message sent successfully to partition {record_metadata.partition}", "SUCCESS")
            
            # Try to consume it
            consumer = KafkaConsumer(
                self.test_topic,
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='latest',
                group_id='large-message-test-group',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                consumer_timeout_ms=10000,
                max_partition_fetch_bytes=10485760
            )
            
            # Ensure assignment before seeking
            consumer.poll(timeout_ms=2000)
            assignments = consumer.assignment()
            start_wait = time.time()
            while not assignments and time.time() - start_wait < 5:
                consumer.poll(timeout_ms=200)
                assignments = consumer.assignment()

            for partition in assignments:
                consumer.seek(partition, record_metadata.offset)
            
            for msg in consumer:
                if msg.value.get('id') == 'large-message-test':
                    self.log(f"Large message received successfully (size: {len(str(msg.value))} bytes)", "SUCCESS")
                    consumer.close()
                    return True
            
            consumer.close()
            self.log("Large message not found in consumer", "WARNING")
            return False
            
        except Exception as e:
            self.log(f"Large message test failed: {str(e)}", "ERROR")
            return False
    
    def test_partitions(self) -> bool:
        """Test message distribution across partitions"""
        self.log("Testing partition distribution...")
        try:
            producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            
            partition_counts = {}
            num_messages = 30
            
            for i in range(num_messages):
                message = {'id': i, 'data': f'partition-test-{i}'}
                future = producer.send(self.test_topic, value=message)
                metadata = future.get(timeout=10)
                partition = metadata.partition
                partition_counts[partition] = partition_counts.get(partition, 0) + 1
            
            producer.close()
            
            self.log(f"Messages distributed across {len(partition_counts)} partitions:", "SUCCESS")
            for partition, count in sorted(partition_counts.items()):
                self.log(f"  Partition {partition}: {count} messages", "INFO")
            
            return len(partition_counts) > 1
            
        except Exception as e:
            self.log(f"Partition test failed: {str(e)}", "ERROR")
            return False
    
    def list_topics(self) -> bool:
        """List all topics in the cluster"""
        self.log("Listing all topics...")
        try:
            admin = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
            topics = admin.list_topics()
            self.log(f"Found {len(topics)} topics:", "SUCCESS")
            for topic in sorted(topics):
                self.log(f"  - {topic}", "INFO")
            admin.close()
            return True
        except Exception as e:
            self.log(f"Failed to list topics: {str(e)}", "ERROR")
            return False
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "="*70)
        print("KAFKA COMPREHENSIVE TEST SUITE")
        print("="*70 + "\n")
        
        tests = [
            ("Connection Test", lambda: self.test_connection()),
            ("Topic Creation", lambda: self.create_topic()),
            ("List Topics", lambda: self.list_topics()),
            ("Producer Test", lambda: self.test_producer(10)),
            ("Consumer Test", lambda: self.test_consumer(15)),
            ("Partition Distribution", lambda: self.test_partitions()),
            ("Large Message Test (5MB)", lambda: self.test_large_message(5.0)),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"\n--- Running: {test_name} ---")
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log(f"Test crashed: {str(e)}", "ERROR")
                failed += 1
            time.sleep(2)  # Brief pause between tests
        
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Total Tests: {passed + failed}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/(passed+failed)*100):.1f}%")
        print("="*70 + "\n")
        
        return failed == 0


if __name__ == "__main__":
    import sys
    
    # Check if custom bootstrap server provided
    bootstrap_servers = sys.argv[1] if len(sys.argv) > 1 else None
    
    print(f"Using Kafka bootstrap servers: {bootstrap_servers or DEFAULT_BOOTSTRAP_SERVERS}")
    
    # Run tests
    test_suite = KafkaTestSuite(bootstrap_servers)
    success = test_suite.run_all_tests()
    
    sys.exit(0 if success else 1)