from datetime import datetime
from pydantic import BaseModel

class BudgetConfig(BaseModel):
    user_id: str
    model: str
    max_budget: float
    window_size_secs: int
    initial_fill_fraction: float
    created_at: datetime
    updated_at: datetime

class BudgetStatus(BaseModel):
    user_id: str
    model: str
    tokens_remaining: float
    burn_rate: float
