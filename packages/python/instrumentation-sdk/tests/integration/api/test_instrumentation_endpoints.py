import pytest
from fastapi.testclient import TestClient
from src.api.rest.v1.app import create_app
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from unittest.mock import patch, AsyncMock
from opentelemetry import trace
import os
os.environ["SKIP_APP_INIT"] = "true"

@pytest.fixture

def test_env():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    
    # Patch instrument_app to use our test provider
    # Since create_app() calls instrument_app(app), we patch it there.
    with patch("src.api.rest.v1.app.instrument_app") as mock_instrument:
        app = create_app()
        # Manually instrument the app instance with our test provider
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor().instrument_app(app, tracer_provider=provider)
        
        client = TestClient(app)
        yield client, exporter, provider

def test_detect_endpoint_integration(test_env):
    client, exporter, provider = test_env
    exporter.clear()
    
    payload = {
        "url": "https://api.openai.com/v1/chat/completions",
        "body": '{"model": "gpt-4"}'
    }
    
    response = client.post("/v1/instrumentation/detect", json=payload)
    
    assert response.status_code == 200
    assert response.json()["provider"] == "openai"
    
    spans = exporter.get_finished_spans()
    request_span = next((s for s in spans if s.name == "POST /v1/instrumentation/detect" and "feature.name" in s.attributes), None)
    
    assert request_span is not None
    attrs = dict(request_span.attributes)
    assert attrs.get("feature.name") == "auto_instrumentation"
    assert attrs.get("service.name") == "instrumentation-sdk-api"

def test_init_endpoint_integration(test_env):
    client, exporter, provider = test_env
    exporter.clear()
    
    with patch("src.features.auto_instrumentation.index._SERVICE.instrument_all"):
        with patch("opentelemetry.trace.get_tracer_provider", return_value=provider):
            response = client.post("/v1/instrumentation/init")
            assert response.status_code == 200
            assert response.json()["success"] is True
            
    spans = exporter.get_finished_spans()
    request_span = next((s for s in spans if s.name == "POST /v1/instrumentation/init" and "feature.name" in s.attributes), None)
    assert request_span is not None
    assert request_span.attributes["feature.name"] == "auto_instrumentation"

@pytest.mark.asyncio
async def test_test_call_endpoint_integration(test_env):
    client, exporter, provider = test_env
    exporter.clear()
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        payload = {"method": "httpx", "provider": "openai"}
        with patch("opentelemetry.trace.get_tracer_provider", return_value=provider):
            response = client.post("/v1/instrumentation/test-call", json=payload)
            assert response.status_code == 200
            assert response.json()["success"] is True

    spans = exporter.get_finished_spans()
    request_span = next((s for s in spans if s.name == "POST /v1/instrumentation/test-call" and "feature.name" in s.attributes), None)
    assert request_span is not None
    assert request_span.attributes["feature.name"] == "auto_instrumentation"

