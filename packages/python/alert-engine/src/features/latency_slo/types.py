from dataclasses import dataclass
from typing import Optional

@dataclass
class LatencySloAlertPayload:
    model: str
    endpoint: str
    severity: str
    burn_rate: float = 0.0
    p95_current: float = 0.0
    p95_baseline: float = 0.0
    p99_current: float = 0.0
    p99_baseline: float = 0.0
    budget_remaining: float = 0.0
    timestamp: Optional[str] = None
