from __future__ import annotations

from datetime import datetime, timezone


def current_utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def hour_bucket_from_timestamp(ts: float) -> int:
    return datetime.fromtimestamp(ts, tz=timezone.utc).hour
