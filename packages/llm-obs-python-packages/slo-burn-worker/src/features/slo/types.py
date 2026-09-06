from dataclasses import dataclass

@dataclass
class BurnRates:
    fast: float
    medium: float
    slow: float

@dataclass
class AlertRequest:
    model: str
    endpoint: str
    severity: str
    burn_rate_fast: float
    burn_rate_medium: float
    burn_rate_slow: float
    budget_remaining_pct: float
    timestamp: str
