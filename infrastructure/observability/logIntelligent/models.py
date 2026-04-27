from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Tuple


@dataclass
class RawLogRecord:
    line_id: str
    message: str
    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ParsedLogRecord:
    raw: RawLogRecord
    template_id: str
    template_text: str
    extracted_fields: Dict[str, str]
    normalized_fields: Dict[str, str]
    embedding: Tuple[float, ...]
    anomaly_score: float
    storage_tier: str
