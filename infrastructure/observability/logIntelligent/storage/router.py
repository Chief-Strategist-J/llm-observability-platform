from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class StorageTierDecision:
    tier: str
    backend: str


class StorageRouter:
    def __init__(self, now_fn=None) -> None:
        self._now_fn = now_fn or (lambda: datetime.now(timezone.utc))

    def route(self, event_time: datetime) -> StorageTierDecision:
        age = self._now_fn() - event_time.astimezone(timezone.utc)
        if age <= timedelta(hours=24):
            return StorageTierDecision(tier="hot", backend="loki")
        if age <= timedelta(days=30):
            return StorageTierDecision(tier="warm", backend="clickhouse")
        return StorageTierDecision(tier="cold", backend="parquet_s3")
