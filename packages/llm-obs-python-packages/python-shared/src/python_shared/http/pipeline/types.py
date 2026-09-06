from typing import Any, Dict, List, Optional, Protocol
from pydantic import BaseModel, Field, ConfigDict

from python_shared.http.resilience import (
    ConcurrencyAdmissionControl,
    FleetRetryBudget,
    TenantRateLimiter,
    StandardCircuitBreaker,
    TenantPartitionedCacheStore,
)

class RequestConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)

    method: str = Field(default="GET")
    url: str = Field(...)
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Optional[Any] = Field(default=None)
    timeout_ms: float = Field(default=10000.0)
    no_cache: bool = Field(default=False)
    cancel_previous: bool = Field(default=False)
    allowed_hosts: Optional[List[str]] = Field(default=None)
    max_body_size_bytes: int = Field(default=10485760)

class PipelineContext:
    def __init__(
        self,
        config: RequestConfig,
        admission_control: Optional[ConcurrencyAdmissionControl] = None,
        retry_budget: Optional[FleetRetryBudget] = None,
        rate_limiter: Optional[TenantRateLimiter] = None,
        circuit_breaker: Optional[StandardCircuitBreaker] = None,
        cache_store: Optional[TenantPartitionedCacheStore] = None,
    ):
        self.config = config
        self.step_index: int = 0
        self.tenant_id: str = "tenant-default"
        self.hashed_request_key: Optional[str] = None
        self.route_template: Optional[str] = None
        self.circuit_key: Optional[str] = None
        self.singleflight_hit: bool = False
        self.cached_response: Optional[Any] = None

        self.admission_control = admission_control or ConcurrencyAdmissionControl()
        self.retry_budget = retry_budget or FleetRetryBudget()
        self.rate_limiter = rate_limiter or TenantRateLimiter()
        self.circuit_breaker = circuit_breaker or StandardCircuitBreaker()
        self.cache_store = cache_store or TenantPartitionedCacheStore()
        self.in_flight_singleflights: Dict[str, Any] = {}

class PipelineStep(Protocol):
    name: str
    description: str
    async def execute(self, ctx: PipelineContext) -> None: ...
