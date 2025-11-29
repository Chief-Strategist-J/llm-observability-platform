import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.kafka.clients.kafka_consumer_client import (
    ConsumerConfig,
    ConsumerRecord
)
from infrastructure.orchestrator.kafka.utils.serializers import StringDeserializer, JSONDeserializer


class TestKafkaConsumer:
    def test_consumer_config_creation(self):
        config = ConsumerConfig(
            bootstrap_servers=["localhost:9092"],
            group_id="test-group",
            client_id="test-consumer",
            auto_offset_reset="earliest"
        )
        
        assert config.bootstrap_servers == ["localhost:9092"]
        assert config.group_id == "test-group"
        assert config.client_id == "test-consumer"
        assert config.auto_offset_reset == "earliest"
    
    def test_consumer_config_defaults(self):
        config = ConsumerConfig(bootstrap_servers=["localhost:9092"])
        
        assert config.client_id == "kafka-consumer"
        assert config.enable_auto_commit is True
        assert config.auto_commit_interval_ms == 5000
        assert config.auto_offset_reset == "latest"
        assert config.max_poll_records == 500
    
    def test_consumer_record_creation(self):
        record = ConsumerRecord(
            topic="test-topic",
            partition=0,
            offset=100,
            timestamp=1234567890,
            key="test-key",
            value="test-value"
        )
        
        assert record.topic == "test-topic"
        assert record.partition == 0
        assert record.offset == 100
        assert record.timestamp == 1234567890
        assert record.key == "test-key"
        assert record.value == "test-value"
    
    def test_string_deserializer(self):
        deserializer = StringDeserializer()
        
        data = b"hello world"
        deserialized = deserializer.deserialize(data)
        
        assert isinstance(deserialized, str)
        assert deserialized == "hello world"
    
    def test_string_deserializer_empty(self):
        deserializer = StringDeserializer()
        
        deserialized = deserializer.deserialize(b"")
        assert deserialized == ""
    
    def test_json_deserializer(self):
        deserializer = JSONDeserializer()
        
        data = b'{"key": "value", "number": 42}'
        deserialized = deserializer.deserialize(data)
        
        assert isinstance(deserialized, dict)
        assert deserialized["key"] == "value"
        assert deserialized["number"] == 42
    
    def test_json_deserializer_empty(self):
        deserializer = JSONDeserializer()
        
        deserialized = deserializer.deserialize(b"")
        assert deserialized is None
    
    def test_consumer_config_session_timeout(self):
        config = ConsumerConfig(
            bootstrap_servers=["localhost:9092"],
            session_timeout_ms=30000,
            heartbeat_interval_ms=10000
        )
        
        assert config.session_timeout_ms == 30000
        assert config.heartbeat_interval_ms == 10000
    
    def test_consumer_config_fetch_settings(self):
        config = ConsumerConfig(
            bootstrap_servers=["localhost:9092"],
            fetch_min_bytes=1024,
            fetch_max_wait_ms=1000,
            max_partition_fetch_bytes=2048576
        )
        
        assert config.fetch_min_bytes == 1024
        assert config.fetch_max_wait_ms == 1000
        assert config.max_partition_fetch_bytes == 2048576
    
    @pytest.mark.parametrize("auto_offset_reset", ["earliest", "latest", "none"])
    def test_consumer_config_offset_reset(self, auto_offset_reset):
        config = ConsumerConfig(
            bootstrap_servers=["localhost:9092"],
            auto_offset_reset=auto_offset_reset
        )
        
        assert config.auto_offset_reset == auto_offset_reset
    
    def test_consumer_record_with_headers(self):
        headers = {"header1": b"value1", "header2": b"value2"}
        
        record = ConsumerRecord(
            topic="test-topic",
            partition=0,
            offset=100,
            timestamp=1234567890,
            key="test-key",
            value="test-value",
            headers=headers
        )
        
        assert record.headers == headers
        assert record.headers["header1"] == b"value1"
