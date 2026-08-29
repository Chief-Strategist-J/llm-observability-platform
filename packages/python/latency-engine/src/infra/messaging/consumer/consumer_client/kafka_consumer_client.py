"""
Algorithm Summary: Managed Kafka Consumer Client.
Encapsulates confluent_kafka Consumer instance for polling and message batch consumption.
Provides graceful subscription, polling timeout management, async offset commits, and consumer loop lifecycle control.
Driven by functional mapping without inline comments or explicit loop conditionals.
"""
from __future__ import annotations
import logging
from typing import Callable
from confluent_kafka import Consumer, Message, KafkaError
from shared.constants.kafka_constants import kafka_constants

logger = logging.getLogger(__name__)

def _is_partition_eof(err: KafkaError | None) -> bool:
    return err is not None and err.code() == KafkaError._PARTITION_EOF

class KafkaConsumerClient:
    def __init__(self, consumer: Consumer, topics: list[str]) -> None:
        self._consumer = consumer
        self._topics = topics
        self._running = False

    def subscribe(self) -> None:
        self._consumer.subscribe(self._topics)

    def poll(self, timeout: float = 1.0) -> Message | None:
        msg = self._consumer.poll(timeout)
        if msg is None:
            return None
        if msg.error():
            _is_partition_eof(msg.error()) or logger.error("Consumer error: %s", msg.error())
            return None
        return msg

    def commit(self, message: Message | None = None, asynchronous: bool = True) -> None:
        try:
            message and self._consumer.commit(message=message, asynchronous=asynchronous) or self._consumer.commit(asynchronous=asynchronous)
        except Exception as exc:
            logger.error("Failed to commit offset: %s", exc)

    def consume_loop(
        self,
        handler: Callable[[Message], None],
        should_stop: Callable[[], bool] | None = None,
        poll_timeout: float = 1.0,
    ) -> None:
        self.subscribe()
        self._running = True
        try:
            while self._running:
                should_stop and should_stop() and setattr(self, "_running", False)
                msg = self.poll(poll_timeout)
                msg and handler(msg)
        finally:
            self.close()

    def close(self) -> None:
        self._running = False
        try:
            self._consumer.close()
        except Exception as exc:
            logger.warning("Error closing Kafka consumer: %s", exc)
