from __future__ import annotations

import logging
from typing import Callable, Any
from confluent_kafka import Consumer, Message, KafkaError

logger = logging.getLogger(__name__)


class KafkaConsumerClient:
    def __init__(self, consumer: Consumer, topics: list[str]) -> None:
        self._consumer = consumer
        self._topics = topics
        self._running = False

    def subscribe((self)) -> None:
        self._consumer.subscribe(self._topics)

    def poll(self, timeout: float = 1.0) -> Message | None:
        msg = self._consumer.poll(timeout)
        if msg is None:
            return None
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                return None
            logger.error("Consumer error: %s", msg.error())
            return None
        return msg

    def commit(self, message: Message | None = None, asynchronous: bool = True) -> None:
        try:
            if message:
                self._consumer.commit(message=message, asynchronous=asynchronous)
            else:
                self._consumer.commit(asynchronous=asynchronous)
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
                if should_stop and should_stop():
                    break
                msg = self.poll(poll_timeout)
                if msg is not None:
                    handler(msg)
        finally:
            self.close()

    def close(self) -> None:
        self._running = False
        try:
            self._consumer.close()
        except Exception as exc:
            logger.warning("Error closing Kafka consumer: %s", exc)
