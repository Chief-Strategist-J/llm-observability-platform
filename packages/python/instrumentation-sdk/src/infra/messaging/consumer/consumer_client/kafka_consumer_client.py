from typing import Callable, Any
from src.infra.messaging.factories.consumer_factory import kafka_consumer_factory

class KafkaConsumerClient:
    def __init__(self) -> None:
        self._factory = kafka_consumer_factory

    def consume_stream(self, topic: str, group_id: str, handler_fn: Callable[[Any], None]) -> None:
        consumer = self._factory.create_consumer(topic, group_id)
        for msg in consumer:
            handler_fn(msg)

kafka_consumer_client = KafkaConsumerClient()
