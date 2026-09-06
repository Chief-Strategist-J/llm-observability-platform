from typing import Any, Dict, Optional, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime, timezone

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HealthStatusResponse(BaseModel):
    status: str = "healthy"
    service_name: str
    version: str = "0.1.0"
    uptime_seconds: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)
