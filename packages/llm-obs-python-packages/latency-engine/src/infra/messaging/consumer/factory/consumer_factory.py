from __future__ import annotations

from typing import Any
from confluent_kafka import Consumer
from infra.messaging.broker.connection_pool import KafkaConnectionPool
from infra.messaging.consumer.consumer_client.kafka_consumer_client import KafkaConsumerClient


class ConsumerFactory:
    @staticmethod
    def create_client(
        group_id: str,
        topics: list[str],
        extra_config: dict[str, Any] | None = None,
    ) -> KafkaConsumerClient:
        pool = KafkaConnectionPool.get_instance()
        raw_consumer = pool.create_consumer(group_id, extra_config)
        return KafkaConsumerClient(raw_consumer, topics)
