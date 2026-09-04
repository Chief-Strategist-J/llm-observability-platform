import os
from typing import Dict, Any, Optional
from confluent_kafka import Producer, Consumer

def get_kafka_producer(bootstrap_servers: Optional[str] = None, config_overrides: Optional[Dict[str, Any]] = None) -> Producer:
    brokers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    config = {
        "bootstrap.servers": brokers,
        "client.id": "platform-python-producer",
        "acks": "all",
    }
    if config_overrides:
        config.update(config_overrides)
    return Producer(config)

def get_kafka_consumer(group_id: str, bootstrap_servers: Optional[str] = None, config_overrides: Optional[Dict[str, Any]] = None) -> Consumer:
    brokers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    config = {
        "bootstrap.servers": brokers,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    }
    if config_overrides:
        config.update(config_overrides)
    return Consumer(config)
