import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.kafka.clients.kafka_admin_client import (
    AdminConfig,
    TopicConfig
)


class TestKafkaAdmin:
    def test_admin_config_creation(self):
        config = AdminConfig(
            bootstrap_servers=["localhost:9092"],
            client_id="test-admin",
            request_timeout_ms=60000
        )
        
        assert config.bootstrap_servers == ["localhost:9092"]
        assert config.client_id == "test-admin"
        assert config.request_timeout_ms == 60000
    
    def test_admin_config_defaults(self):
        config = AdminConfig(bootstrap_servers=["localhost:9092"])
        
        assert config.client_id == "kafka-admin"
        assert config.request_timeout_ms == 30000
    
    def test_topic_config_creation(self):
        topic_config = TopicConfig(
            name="test-topic",
            num_partitions=3,
            replication_factor=2,
            config={"retention.ms": "86400000"}
        )
        
        assert topic_config.name == "test-topic"
        assert topic_config.num_partitions == 3
        assert topic_config.replication_factor == 2
        assert topic_config.config["retention.ms"] == "86400000"
    
    def test_topic_config_defaults(self):
        topic_config = TopicConfig(name="test-topic")
        
        assert topic_config.num_partitions == 1
        assert topic_config.replication_factor == 1
        assert topic_config.config is None
    
    @pytest.mark.parametrize("num_partitions,replication_factor", [
        (1, 1),
        (3, 1),
        (5, 2),
        (10, 3),
    ])
    def test_topic_config_various_settings(self, num_partitions, replication_factor):
        topic_config = TopicConfig(
            name="test-topic",
            num_partitions=num_partitions,
            replication_factor=replication_factor
        )
        
        assert topic_config.num_partitions == num_partitions
        assert topic_config.replication_factor == replication_factor
    
    def test_topic_config_with_multiple_configs(self):
        configs = {
            "retention.ms": "86400000",
            "compression.type": "gzip",
            "max.message.bytes": "1048576"
        }
        
        topic_config = TopicConfig(
            name="test-topic",
            config=configs
        )
        
        assert len(topic_config.config) == 3
        assert topic_config.config["retention.ms"] == "86400000"
        assert topic_config.config["compression.type"] == "gzip"
        assert topic_config.config["max.message.bytes"] == "1048576"
