import pytest
from fastapi.testclient import TestClient
from src.api.rest.v1.app import create_app
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from unittest.mock import patch
import os
import uuid
from src import should_sample

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

def test_sampling_endpoint_sampled(test_env):
    client, exporter, provider = test_env
    sampled_id = None
    while sampled_id is None:
        u = uuid.uuid4()
        if should_sample(u):
            sampled_id = u
    
    payload = {"span_id": str(sampled_id)}
    response = client.post("/v1/sampling/should-sample", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_sampled"] is True

def test_sampling_endpoint_unsampled(test_env):
    client, exporter, provider = test_env
    unsampled_id = None
    while unsampled_id is None:
        u = uuid.uuid4()
        if not should_sample(u):
            unsampled_id = u
    
    payload = {"span_id": str(unsampled_id)}
    response = client.post("/v1/sampling/should-sample", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_sampled"] is False

def test_sampling_endpoint_invalid_payload(test_env):
    client, exporter, provider = test_env
    response = client.post("/v1/sampling/should-sample", json={})
    assert response.status_code == 422

def test_sampling_endpoint_exception_handling(test_env):
    client, exporter, provider = test_env
    payload = {"span_id": "test"}
    with patch("src.api.rest.v1.handlers.deterministic_sampling.should_sample", side_effect=ValueError("Invalid UUID format")):
        response = client.post("/v1/sampling/should-sample", json=payload)
    assert response.status_code == 500
    assert "Invalid UUID format" in response.json()["detail"]
