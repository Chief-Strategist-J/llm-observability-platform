import os
import pytest
from src.infra.messaging.broker.broker_config import KafkaBrokerConfig
from src.infra.messaging.producer.factory.producer_factory import KafkaProducerFactory

def test_kafka_broker_config_defaults():
    config = KafkaBrokerConfig()
    assert isinstance(config.bootstrap_servers, list)
    assert len(config.bootstrap_servers) > 0
    assert config.acks == "all"
    assert config.compression_type == "gzip"

def test_kafka_client_factory_singleton():
    factory1 = KafkaProducerFactory.get_instance()
    factory2 = KafkaProducerFactory.get_instance()
    assert factory1 is factory2
