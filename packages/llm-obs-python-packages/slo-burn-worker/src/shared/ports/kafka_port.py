from typing import Protocol, Dict, Any

class KafkaPort(Protocol):
    def publish_alert(self, topic: str, key: str, payload: Dict[str, Any]) -> None:
        """Publishes alert payload to the specified Kafka topic."""
        ...
