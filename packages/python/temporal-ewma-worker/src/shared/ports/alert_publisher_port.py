from typing import Protocol
from shared.types.ewma_types import AnomalyPayload


class AlertPublisherPort(Protocol):
    def publish_anomaly(self, payload: AnomalyPayload) -> None: ...
