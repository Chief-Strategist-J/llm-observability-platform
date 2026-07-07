from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class ForecastData:
    service: str
    model: str
    mean: float
    p10: float
    p90: float
    forecast_time: datetime
    source: str

@dataclass
class CostBreachRisk:
    service: str
    model: str
    budget_limit: Optional[float]
    predicted_cost_p90_usd: float
    breach_predicted: bool
    forecast_time: datetime

@dataclass
class ForecastSummaryItem:
    service: str
    model: str
    forecast_time: datetime
    mean: float
    p10: float
    p90: float
    budget_limit: Optional[float]
    breach_predicted: bool

@dataclass
class ForecastSummary:
    forecasts: List[ForecastSummaryItem]
