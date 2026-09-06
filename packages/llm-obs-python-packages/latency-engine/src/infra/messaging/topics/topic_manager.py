from __future__ import annotations

import logging
from confluent_kafka.admin import AdminClient
from infra.messaging.broker.broker_config import KafkaBrokerConfig

logger = logging.getLogger(__name__)


class TopicManager:
    def __init__(self, config: KafkaBrokerConfig | None = None) -> None:
        self.config = config or KafkaBrokerConfig.from_env()

    def list_topics(self, timeout: float = 5.0) -> list[str]:
        admin = AdminClient(self.config.to_confluent_config())
        cluster_meta = admin.list_topics(timeout=timeout)
        return list(cluster_meta.topics.keys())

    def topic_exists(self, topic_name: str, timeout: float = 5.0) -> bool:
        return topic_name in self.list_topics(timeout)
