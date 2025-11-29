import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.kafka.clients.kafka_producer_client import (
    KafkaProducerClient,
    ProducerConfig,
    ProducerRecord
)
from infrastructure.orchestrator.kafka.utils.serializers import StringSerializer, JSONSerializer
from infrastructure.orchestrator.kafka.utils.partition_selector import HashPartitioner, RoundRobinPartitioner


class TestKafkaProducer:
    def test_producer_config_creation(self):
        config = ProducerConfig(
            bootstrap_servers=["localhost:9092"],
            client_id="test-producer",
            acks="all",
            enable_idempotence=True
        )
        
        assert config.bootstrap_servers == ["localhost:9092"]
        assert config.client_id == "test-producer"
        assert config.acks == "all"
        assert config.enable_idempotence is True
    
    def test_producer_record_creation(self):
        record = ProducerRecord(
            topic="test-topic",
            value="test-value",
            key="test-key",
            partition=0
        )
        
        assert record.topic == "test-topic"
        assert record.value == "test-value"
        assert record.key == "test-key"
        assert record.partition == 0
    
    def test_string_serializer(self):
        serializer = StringSerializer()
        
        data = "hello world"
        serialized = serializer.serialize(data)
        
        assert isinstance(serialized, bytes)
        assert serialized == b"hello world"
    
    def test_json_serializer(self):
        serializer = JSONSerializer()
        
        data = {"key": "value", "number": 42}
        serialized = serializer.serialize(data)
        
        assert isinstance(serialized, bytes)
        assert b'"key"' in serialized
        assert b'"value"' in serialized
    
    def test_hash_partitioner(self):
        partitioner = HashPartitioner()
        
        key = b"test-key"
        num_partitions = 3
        
        partition1 = partitioner.select_partition(key, num_partitions)
        partition2 = partitioner.select_partition(key, num_partitions)
        
        assert 0 <= partition1 < num_partitions
        assert partition1 == partition2
    
    def test_hash_partitioner_none_key(self):
        partitioner = HashPartitioner()
        
        partition = partitioner.select_partition(None, 3)
        assert partition == 0
    
    def test_round_robin_partitioner(self):
        partitioner = RoundRobinPartitioner()
        
        num_partitions = 3
        partitions = []
        
        for i in range(6):
            partition = partitioner.select_partition(None, num_partitions)
            partitions.append(partition)
        
        assert all(0 <= p < num_partitions for p in partitions)
        assert len(set(partitions)) > 1
    
    def test_murmur2_hash_consistency(self):
        partitioner = HashPartitioner()
        
        key = b"consistent-key"
        hash1 = partitioner._murmur2_hash(key)
        hash2 = partitioner._murmur2_hash(key)
        
        assert hash1 == hash2
    
    def test_producer_config_defaults(self):
        config = ProducerConfig(bootstrap_servers=["localhost:9092"])
        
        assert config.client_id == "kafka-producer"
        assert config.acks == "all"
        assert config.retries == 3
        assert config.enable_idempotence is True
    
    @pytest.mark.parametrize("key,num_partitions", [
        (b"key1", 3),
        (b"key2", 5),
        (b"key3", 10),
    ])
    def test_hash_partitioner_distribution(self, key, num_partitions):
        partitioner = HashPartitioner()
        partition = partitioner.select_partition(key, num_partitions)
        
        assert 0 <= partition < num_partitions
