from __future__ import annotations

import logging
import threading
from typing import Any
from confluent_kafka import Consumer, Producer

from infra.messaging.broker.broker_config import KafkaBrokerConfig

logger = logging.getLogger(__name__)


class KafkaConnectionPool:
    _instance: KafkaConnectionPool | None = None
    _lock = threading.Lock()

    def __init__(self, config: KafkaBrokerConfig | None = None) -> None:
        self.config = config or KafkaBrokerConfig.from_env()
        self._producers: dict[str, Producer] = {}
        self._pool_lock = threading.Lock()

    @classmethod
    def get_instance(cls, config: KafkaBrokerConfig | None = None) -> KafkaConnectionPool:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(config)
            return cls._instance

    def get_producer(self, client_id_suffix: str = "") -> Producer:
        key = f"producer_{client_id_suffix}"
        with self._pool_lock:
            if key not in self._producers:
                conf = self.config.to_confluent_config()
                if client_id_suffix:
                    conf["client.id"] = f"{conf['client.id']}-{client_id_suffix}"
                logger.info("Initializing cached Kafka Producer for %s", key)
                self._producers[key] = Producer(conf)
            return self._producers[key]

    def create_consumer(self, group_id: str, extra_config: dict[str, Any] | None = None) -> Consumer:
        conf = self.config.to_confluent_config()
        conf["group.id"] = group_id
        conf["enable.auto.commit"] = False
        conf["auto.offset.reset"] = "earliest"
        if extra_config:
            conf.update(extra_config)
        logger.info("Creating new Kafka Consumer for group_id=%s", group_id)
        return Consumer(conf)

    def close_all(self) -> None:
        with self._pool_lock:
            for key, producer in self._producers.items():
                logger.info("Flushing Kafka Producer %s", key)
                producer.flush(timeout=5)
            self._producers.clear()
