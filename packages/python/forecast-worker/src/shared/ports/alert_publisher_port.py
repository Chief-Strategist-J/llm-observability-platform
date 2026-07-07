from typing import Protocol, Dict, Any

class AlertPublisherPort(Protocol):
    def publish_predicted_breach(self, payload: Dict[str, Any]) -> None:
        """
        Publish a predicted budget breach alert event to Kafka.
        """
        ...
