from __future__ import annotations

import logging
from confluent_kafka.admin import AdminClient

from infra.messaging.broker.broker_config import KafkaBrokerConfig

logger = logging.getLogger(__name__)


class KafkaHealthCheck:
    """Probes Kafka cluster health and metadata availability."""

    def __init__(self, config: KafkaBrokerConfig | None = None) -> None:
        self.config = config or KafkaBrokerConfig.from_env()

    def check_health(self, timeout_seconds: float = 3.0) -> dict[str, str | bool | int]:
        """Queries cluster metadata to ascertain health status."""
        try:
            admin = AdminClient(self.config.to_confluent_config())
            cluster_meta = admin.list_topics(timeout=timeout_seconds)
            broker_count = len(cluster_meta.brokers)
            topic_count = len(cluster_meta.topics)
            is_healthy = broker_count > 0

            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "healthy": is_healthy,
                "brokers_available": broker_count,
                "topics_count": topic_count,
            }
        except Exception as exc:
            logger.error("Kafka broker health check failed: %s", exc)
            return {
                "status": "unhealthy",
                "healthy": False,
                "error": str(exc),
            }
