from __future__ import annotations

from confluent_kafka import Producer
from infra.messaging.broker.connection_pool import KafkaConnectionPool
from infra.messaging.producer.producer_client.kafka_producer_client import KafkaProducerClient


class ProducerFactory:
    """Factory for creating managed KafkaProducerClient instances."""

    @staticmethod
    def create_client(client_id_suffix: str = "") -> KafkaProducerClient:
        pool = KafkaConnectionPool.get_instance()
        raw_producer = pool.get_producer(client_id_suffix)
        return KafkaProducerClient(raw_producer)
