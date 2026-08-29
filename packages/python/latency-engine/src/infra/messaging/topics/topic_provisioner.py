from __future__ import annotations
import logging
import socket
from confluent_kafka.admin import AdminClient, NewTopic
from infra.messaging.broker.broker_config import KafkaBrokerConfig

logger = logging.getLogger(__name__)

def is_socket_reachable(host_port: str, timeout: float = 0.2) -> bool:
    try:
        parts = host_port.split(",")[0].strip().split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 9092
        socket.gethostbyname(host)
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

class TopicProvisioner:
    def __init__(self, config: KafkaBrokerConfig | None = None) -> None:
        self.config = config or KafkaBrokerConfig.from_env()

    def provision_topics(
        self,
        topics: list[tuple[str, int, int]],
    ) -> dict[str, bool]:
        if not is_socket_reachable(self.config.bootstrap_servers):
            logger.warning("Kafka broker unreachable at %s — skipping python topic provisioning.", self.config.bootstrap_servers)
            return {name: False for name, _, _ in topics}

        try:
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
        except Exception as exc:
            logger.warning("AdminClient creation failed: %s", exc)
            return {name: False for name, _, _ in topics}
