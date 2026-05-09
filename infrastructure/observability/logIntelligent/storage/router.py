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
        """
        Route a log event to a storage tier based on its age.
        
        Args:
            event_time: The event timestamp. Must be timezone-aware.
            
        Returns:
            StorageTierDecision with tier ('hot', 'warm', or 'cold') and backend.
            
        Raises:
            ValueError: If event_time is naive (not timezone-aware).
        """
        # Validate and normalize event_time: must be timezone-aware
        if event_time.tzinfo is None:
            raise ValueError(
                f"event_time must be timezone-aware (got naive datetime: {event_time}). "
                "Use datetime.now(timezone.utc) or attach tzinfo before calling route()."
            )
        
        # Normalize both times to UTC for consistent age calculation
        event_time_utc = event_time.astimezone(timezone.utc)
        now_utc = self._now_fn()
        
        # Ensure now_utc is also timezone-aware
        if now_utc.tzinfo is None:
            raise ValueError(
                f"now_fn() returned a naive datetime: {now_utc}. "
                "It must return a timezone-aware datetime."
            )
        
        # Normalize to UTC
        now_utc = now_utc.astimezone(timezone.utc)
        
        # Calculate age and route
        age = now_utc - event_time_utc
        if age <= timedelta(hours=24):
            return StorageTierDecision(tier="hot", backend="loki")
        if age <= timedelta(days=30):
            return StorageTierDecision(tier="warm", backend="clickhouse")
        return StorageTierDecision(tier="cold", backend="parquet_s3")
