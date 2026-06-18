import json
import logging
from typing import Dict, Any
from confluent_kafka import Producer
from shared.ports.kafka_port import KafkaPort
from shared.tracing.tracer import trace_span

logger = logging.getLogger(__name__)

class KafkaAlertAdapter(KafkaPort):
    def __init__(self, bootstrap_servers: str):
        self.producer = Producer({"bootstrap.servers": bootstrap_servers})

    def publish_alert(self, topic: str, key: str, payload: Dict[str, Any]) -> None:
        try:
            with trace_span(
                "kafka:publish_alert",
                attributes={
                    "messaging.system": "kafka",
                    "messaging.destination": topic,
                    "messaging.kafka.message_key": key,
                },
            ):
                value = json.dumps(payload).encode("utf-8")
                self.producer.produce(
                    topic=topic,
                    key=key.encode("utf-8"),
                    value=value,
                )
                self.producer.flush()
                logger.info("Successfully published SLO alert to topic=%s key=%s", topic, key)
        except Exception as e:
            logger.error("Failed to publish alert to topic %s: %s", topic, e)
            raise
