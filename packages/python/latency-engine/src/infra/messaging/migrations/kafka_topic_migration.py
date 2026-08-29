from __future__ import annotations

import logging
from infra.messaging.topics.topic_provisioner import TopicProvisioner
from infra.messaging.broker.broker_config import KafkaBrokerConfig

logger = logging.getLogger(__name__)


class KafkaTopicMigration:
    def __init__(self, config: KafkaBrokerConfig | None = None) -> None:
        self.provisioner = TopicProvisioner(config)

    def run_migrations(self) -> None:
        required_topics = [
            ("llm.spans.raw", 3, 1),
            ("latency.anomalies.v1", 3, 1),
        ]
        logger.info("Executing Kafka topic migrations...")
        results = self.provisioner.provision_topics(required_topics)
        logger.info("Kafka topic migrations completed: %s", results)
