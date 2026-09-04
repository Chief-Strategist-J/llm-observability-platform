import pytest
import time
from python_shared.discovery import (
    resolve_service_endpoint,
    resolve_service_url_sync,
    ServiceResolver,
    ServiceResolverOptions,
    ServiceRegistryManager,
    ServiceRegistryManagerOptions,
    DEFAULT_SERVICE_CATALOG,
    ServiceInstanceModel,
    HealthCheckSpec,
)

def test_resolve_service_endpoint_fallback():
    endpoint = resolve_service_endpoint("quality-engine")
    assert endpoint == "http://quality-engine.internal:8003"

    endpoint_unknown = resolve_service_endpoint("unknown-service")
    assert endpoint_unknown == "http://unknown-service:8000"

    endpoint_custom = resolve_service_endpoint("unknown-service", fallback_url="http://custom:9000")
    assert endpoint_custom == "http://custom:9000"

def test_service_resolver_caching():
    resolver = ServiceResolver(ServiceResolverOptions(ttl_seconds=5.0))
    
    endpoint = resolver.resolve_sync("quality-engine")
    assert endpoint == "http://quality-engine.internal:8003"

    resolver._cache["quality-engine"] = ("http://cached-quality:8003", [], time.time())
    cached_endpoint = resolver.resolve_sync("quality-engine")
    assert cached_endpoint == "http://cached-quality:8003"

    resolver.clear_cache()
    cleared_endpoint = resolver.resolve_sync("quality-engine")
    assert cleared_endpoint == "http://quality-engine.internal:8003"

@pytest.mark.asyncio
async def test_service_resolver_async():
    resolver = ServiceResolver(ServiceResolverOptions(ttl_seconds=5.0))
    endpoint = await resolver.resolve("alert-engine")
    assert endpoint == "http://alert-engine.internal:8004"

def test_service_instance_model():
    instance = ServiceInstanceModel(
        name="test-service",
        host="localhost",
        port=8080,
        protocol="http",
    )
    assert instance.endpoint == "http://localhost:8080"
    assert instance.weight == 100
    assert instance.status == 0

def test_service_registry_manager_initialization():
    options = ServiceRegistryManagerOptions(
        name="quality-engine",
        host="quality.internal",
        port=8003,
    )
    mgr = ServiceRegistryManager(options)
    assert mgr.options.name == "quality-engine"
    assert mgr.options.host == "quality.internal"
    assert mgr.options.port == 8003
    assert mgr.instance_id is None
