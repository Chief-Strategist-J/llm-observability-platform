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


def test_metrics_health_endpoint(test_env):
    client, exporter, provider = test_env
    response = client.get("/v1/metrics/health")
    assert response.status_code == 200
    data = response.json()
    assert "initialized" in data
    assert "message" in data


def test_metrics_record_single_span(test_env):
    client, exporter, provider = test_env
    payload = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "test-service",
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "latency_ms_total": 200,
        "status": "success",
    }
    response = client.post("/v1/metrics/record", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["recorded"] is True
    assert data["cost_usd_micro"] is not None
    assert data["cost_usd_micro"] > 0


def test_metrics_record_returns_price_version(test_env):
    client, exporter, provider = test_env
    payload = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "test-service",
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "latency_ms_total": 300,
        "status": "success",
    }
    response = client.post("/v1/metrics/record", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["price_version"] is not None


def test_metrics_record_unknown_model_no_cost(test_env):
    client, exporter, provider = test_env
    payload = {
        "model": "claude-3-opus",
        "provider": "anthropic",
        "service_name": "test-service",
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "latency_ms_total": 200,
        "status": "success",
    }
    response = client.post("/v1/metrics/record", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["recorded"] is True
    assert data["cost_usd_micro"] is None


def test_metrics_record_batch(test_env):
    client, exporter, provider = test_env
    payload = {
        "spans": [
            {
                "model": "gpt-4o",
                "provider": "openai",
                "service_name": "batch-svc",
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "latency_ms_total": 100,
                "status": "success",
            },
            {
                "model": "gpt-3.5-turbo",
                "provider": "openai",
                "service_name": "batch-svc",
                "prompt_tokens": 200,
                "completion_tokens": 100,
                "latency_ms_total": 150,
                "status": "success",
            },
            {
                "model": "claude-3-opus",
                "provider": "anthropic",
                "service_name": "batch-svc",
                "latency_ms_total": 300,
                "status": "error",
            },
        ]
    }
    response = client.post("/v1/metrics/record-batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["recorded_count"] == 3


def test_metrics_record_empty_batch(test_env):
    client, exporter, provider = test_env
    payload = {"spans": []}
    response = client.post("/v1/metrics/record-batch", json=payload)
    assert response.status_code == 200
    assert response.json()["recorded_count"] == 0


def test_metrics_record_minimal_payload(test_env):
    client, exporter, provider = test_env
    payload = {}
    response = client.post("/v1/metrics/record", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["recorded"] is True


def test_metrics_record_invalid_payload(test_env):
    client, exporter, provider = test_env
    response = client.post("/v1/metrics/record", json={"prompt_tokens": "not_a_number"})
    assert response.status_code == 422


def test_metrics_record_with_pii_and_injection(test_env):
    client, exporter, provider = test_env
    payload = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "security-svc",
        "pii_detected": True,
        "injection_attempt": True,
        "latency_ms_total": 100,
        "status": "success",
    }
    response = client.post("/v1/metrics/record", json=payload)
    assert response.status_code == 200
    assert response.json()["recorded"] is True


def test_metrics_record_with_finish_reason(test_env):
    client, exporter, provider = test_env
    payload = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-svc",
        "finish_reason": "content_filter",
        "latency_ms_total": 100,
        "status": "success",
    }
    response = client.post("/v1/metrics/record", json=payload)
    assert response.status_code == 200
    assert response.json()["recorded"] is True


def test_metrics_init_endpoint(test_env):
    client, exporter, provider = test_env
    with patch("src.api.rest.v1.handlers.metrics.init_metrics_pipeline"):
        response = client.post("/v1/metrics/init", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["initialized"] is True
