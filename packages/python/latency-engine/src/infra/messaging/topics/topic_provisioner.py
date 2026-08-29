from __future__ import annotations

import logging
from confluent_kafka.admin import AdminClient, NewTopic
from infra.messaging.broker.broker_config import KafkaBrokerConfig

logger = logging.getLogger(__name__)


class TopicProvisioner:
    def __init__(self, config: KafkaBrokerConfig | None = None) -> None:
        self.config = config or KafkaBrokerConfig.from_env()

    def provision_topics(
        self,
        topics: list[tuple[str, int, int]],
    ) -> dict[str, bool]:
        admin = AdminClient(self.config.to_confluent_config())
        new_topics = [
            NewTopic(topic=name, num_partitions=num_parts, replication_factor=repl_factor)
            for name, num_parts, repl_factor in topics
        ]

        futures = admin.create_topics(new_topics)
        results: dict[str, bool] = {}
        for topic, future in futures.items():
            try:
                future.result()
                results[topic] = True
                logger.info("Successfully provisioned topic %s", topic)
            except Exception as exc:
                results[topic] = False
                logger.warning("Topic provisioning skipped or failed for %s: %s", topic, exc)
        return results
