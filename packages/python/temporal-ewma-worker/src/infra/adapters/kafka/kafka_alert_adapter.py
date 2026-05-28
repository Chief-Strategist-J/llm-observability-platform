import json
from dataclasses import asdict
from confluent_kafka import Producer
from shared.ports.alert_publisher_port import AlertPublisherPort
from shared.types.ewma_types import AnomalyPayload


class KafkaAlertAdapter(AlertPublisherPort):
    def __init__(self, bootstrap_servers: str):
        self.producer = Producer({"bootstrap.servers": bootstrap_servers})

    def publish_anomaly(self, payload: AnomalyPayload) -> None:
        topic = "alerts.cost.anomaly"
        payload_dict = asdict(payload)
        self.producer.produce(
            topic=topic,
            key=f"{payload.service}:{payload.model}",
            value=json.dumps(payload_dict).encode("utf-8"),
        )
        self.producer.flush()

    def publish_integrity_mismatch(
        self, dimension: str, key: str, redis_sum: int, clickhouse_sum: int
    ) -> None:
        topic = "alerts.cost.integrity_mismatch"
        payload = {
            "dimension": dimension,
            "key": key,
            "redis_sum": redis_sum,
            "clickhouse_sum": clickhouse_sum,
        }
        self.producer.produce(
            topic=topic,
            key=f"{dimension}:{key}",
            value=json.dumps(payload).encode("utf-8"),
        )
        self.producer.flush()

