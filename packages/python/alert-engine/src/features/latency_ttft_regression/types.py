from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class LatencyTtftRegressionAlertPayload:
    model: str
    current: float
    baseline: float
    hour_of_day: int
    timestamp: Optional[str] = None
