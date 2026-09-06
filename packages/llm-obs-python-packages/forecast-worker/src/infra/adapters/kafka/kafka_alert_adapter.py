import json
from typing import Dict, Any
from confluent_kafka import Producer
from shared.ports.alert_publisher_port import AlertPublisherPort

class KafkaAlertAdapter(AlertPublisherPort):
    def __init__(self, bootstrap_servers: str):
        self.producer = Producer({"bootstrap.servers": bootstrap_servers})

    def publish_predicted_breach(self, payload: Dict[str, Any]) -> None:
        topic = "alerts.cost.predicted_breach"
        key = f"{payload.get('service') or payload.get('user_id')}:{payload.get('model')}"
        self.producer.produce(
            topic=topic,
            key=key.encode("utf-8"),
            value=json.dumps(payload).encode("utf-8"),
        )
        self.producer.flush()
