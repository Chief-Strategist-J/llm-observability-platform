import pytest
from python_shared.http import (
    HTTP_CONSTANTS,
    ResilientHttpClient,
    httpClient,
    CircuitBreaker,
    StandardCircuitBreaker,
    RetryPolicy,
    FleetRetryBudget,
    ConcurrencyAdmissionControl,
    TenantRateLimiter,
    TenantPartitionedCacheStore,
    RequestConfig,
    PipelineContext,
    HttpPipelineRunner,
    pipeline_runner,
    extract_or_generate_correlation_id,
    build_standard_headers,
)

def test_resilience_fleet_retry_budget():
    budget = FleetRetryBudget(max_retry_ratio=0.2, min_requests_threshold=5)
    for _ in range(10):
        budget.record_request()
    assert budget.can_retry() is True

def test_resilience_concurrency_admission():
    control = ConcurrencyAdmissionControl(max_capacity=2)
    assert control.acquire() is True
    assert control.acquire() is True
    assert control.acquire() is False
    control.release()
    assert control.acquire() is True

def test_resilience_tenant_cache():
    store = TenantPartitionedCacheStore(max_partition_size=10)
    store.set("tenant-1", "key1", "val1", ttl_ms=5000)
    assert store.get("tenant-1", "key1") == "val1"
    store.clear("tenant-1")
    assert store.get("tenant-1", "key1") is None

def test_standard_circuit_breaker():
    breaker = StandardCircuitBreaker(failure_threshold=2)
    key = breaker.get_circuit_key("tenant-1", "/api/test")
    assert breaker.can_execute(key) is True
    breaker.on_failure(key)
    breaker.on_failure(key)
    assert breaker.can_execute(key) is False

@pytest.mark.asyncio
async def test_pipeline_runner():
    config = RequestConfig(method="GET", url="http://localhost:8000/api/health")
    ctx = PipelineContext(config=config)
    runner = HttpPipelineRunner()
    res_ctx = await runner.run(ctx)
    assert res_ctx.step_index >= 1
