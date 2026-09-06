from typing import Protocol
from shared.types.ewma_types import EwmaRecord


class PostgresPort(Protocol):
    def get_baseline(
        self, service: str, model: str, hour_of_week: int
    ) -> EwmaRecord | None: ...

    def upsert_baseline(self, record: EwmaRecord) -> None: ...
