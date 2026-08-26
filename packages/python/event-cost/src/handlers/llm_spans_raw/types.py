from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class RawSpanEvent:
    span_id: str
    trace_id: str
    service_name: str
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd_micro: int
    price_version: str
    timestamp_utc: datetime
    user_id: str = ""
    org_id: str = ""
    project_id: str = ""
    estimated_tokens: int = 0
    raw_bytes: bytes = field(default=b"", repr=False)


@dataclass(frozen=True)
class FenwickUpdate:
    dimension: str
    window: str
    key: str
    delta: int


@dataclass(frozen=True)
class TokenBucketDelta:
    bucket_key: str
    delta_tokens: int


@dataclass
class HandlerResult:
    processed_count: int = 0
    dlq_count: int = 0
    mismatch_count: int = 0
