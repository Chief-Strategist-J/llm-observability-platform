import pytest
from fastapi.testclient import TestClient
from src.api.rest.v1.app import create_app
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from unittest.mock import patch
import os

os.environ["SKIP_APP_INIT"] = "true"

@pytest.fixture
def test_env():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    with patch("src.api.rest.v1.app.instrument_app"):
        app = create_app()
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor().instrument_app(app, tracer_provider=provider)
        client = TestClient(app)
        yield client, exporter, provider

def test_pii_injection_scan_endpoint_no_pii(test_env):
    client, exporter, provider = test_env
    payload = {
        "prompt": "hello world"
    }
    
    response = client.post("/v1/pii-injection/scan", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["pii_detected"] is False
    assert data["injection_attempt"] is False

def test_pii_injection_scan_endpoint_with_pii(test_env):
    client, exporter, provider = test_env
    payload = {
        "prompt": "my email is test@example.com"
    }
    
    response = client.post("/v1/pii-injection/scan", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["pii_detected"] is True
    assert data["injection_attempt"] is False

def test_pii_injection_scan_endpoint_with_injection(test_env):
    client, exporter, provider = test_env
    payload = {
        "prompt": "union select username, password from users"
    }
    
    response = client.post("/v1/pii-injection/scan", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["pii_detected"] is False
    assert data["injection_attempt"] is True

def test_pii_injection_scan_endpoint_invalid_payload(test_env):
    client, exporter, provider = test_env
    
    response = client.post("/v1/pii-injection/scan", json={})
    assert response.status_code == 422
    
    response_wrong_type = client.post("/v1/pii-injection/scan", json={"prompt": 123})
    assert response_wrong_type.status_code == 422

def test_pii_injection_scan_endpoint_exception_handling(test_env):
    client, exporter, provider = test_env
    payload = {
        "prompt": "hello"
    }
    
    with patch("src.api.rest.v1.handlers.pii_injection.scan_prompt", side_effect=ValueError("Database connection failed")):
        response = client.post("/v1/pii-injection/scan", json=payload)
        
    assert response.status_code == 500
    assert "Database connection failed" in response.json()["detail"]

def test_pii_injection_scan_endpoint_list_payload(test_env):
    client, exporter, provider = test_env
    payload = {
        "prompt": [
            {"role": "user", "content": "my email is test@example.com"},
            {"role": "assistant", "content": "hello"}
        ]
    }
    
    response = client.post("/v1/pii-injection/scan", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["pii_detected"] is True
    assert data["injection_attempt"] is False
