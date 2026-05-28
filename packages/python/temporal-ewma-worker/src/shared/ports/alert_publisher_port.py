from typing import Protocol
from shared.types.ewma_types import AnomalyPayload


class AlertPublisherPort(Protocol):
    def publish_anomaly(self, payload: AnomalyPayload) -> None: ...

    def publish_integrity_mismatch(
        self, dimension: str, key: str, redis_sum: int, clickhouse_sum: int
    ) -> None: ...

