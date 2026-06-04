from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class BaselineRecomputeResult:
    model: str
    endpoint: str
    prompt_type: str
    avg_score: float
    sample_count: int

@dataclass(frozen=True)
class DailyRollupRecord:
    rollup_date: date
    model: str
    endpoint: str
    prompt_type: str
    avg_composite_score: float
    flag_count: int
    sample_count: int
