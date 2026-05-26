from dataclasses import dataclass
from datetime import datetime


@dataclass
class EwmaRecord:
    service: str
    model: str
    hour_of_week: int
    ewma_value: float
    sample_count: int
    is_cold_start: bool
    updated_at: datetime | None = None


@dataclass
class ClusterCost:
    cluster_id: str
    cost: float


@dataclass
class AnomalyPayload:
    service: str
    model: str
    hour_of_week: int
    current_cost: float
    ewma_value: float
    threshold_value: float
    sample_count: int
    timestamp: str
    cluster_drilldown: list[ClusterCost]
