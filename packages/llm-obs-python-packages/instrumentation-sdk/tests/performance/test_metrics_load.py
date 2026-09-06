import pytest
import random
from fastapi.testclient import TestClient
from src.api.rest.v1.app import create_app
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from unittest.mock import patch
import os

os.environ["SKIP_APP_INIT"] = "true"

_MODELS = [
    {"model": "gpt-4o", "provider": "openai"},
    {"model": "gpt-3.5-turbo", "provider": "openai"},
    {"model": "claude-3-opus", "provider": "anthropic"},
    {"model": "claude-3-5-sonnet", "provider": "anthropic"},
    {"model": "llama-3-70b", "provider": "meta"},
    {"model": "gemini-1.5-pro", "provider": "google"},
]

_SERVICES = ["chat-service", "agent-service", "rag-pipeline", "summarizer-tool"]
_STATUSES = ["success"] * 9 + ["error"]
_FINISH_REASONS = ["stop", "stop", "stop", "length", "content_filter"]


def _random_span() -> dict:
    model = random.choice(_MODELS)
    status = random.choice(_STATUSES)
    latency_total = random.randint(100, 3000)
    return {
        "model": model["model"],
        "provider": model["provider"],
        "service_name": random.choice(_SERVICES),
        "prompt_tokens": random.randint(50, 2000),
        "completion_tokens": random.randint(10, 1000),
        "latency_ms_total": latency_total,
        "latency_ms_ttft": random.randint(20, min(latency_total, 500)),
        "status": status,
        "pii_detected": random.random() < 0.05,
        "injection_attempt": random.random() < 0.03,
        "finish_reason": random.choice(_FINISH_REASONS) if status == "success" else None,
        "retry_count": random.randint(0, 2),
    }


@pytest.fixture(scope="module")
def load_client():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    with patch("src.api.rest.v1.app.instrument_app"):
        app = create_app()
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor().instrument_app(app, tracer_provider=provider)
        yield TestClient(app)


@pytest.mark.performance
def test_load_100_individual_spans(load_client):
    errors = []
    for _ in range(100):
        resp = load_client.post("/v1/metrics/record", json=_random_span())
        if resp.status_code != 200:
            errors.append(resp.status_code)
        elif not resp.json().get("recorded"):
            errors.append("recorded=False")
    assert not errors, f"Failures during load: {errors[:5]}"


@pytest.mark.performance
def test_load_batch_50_spans(load_client):
    payload = {"spans": [_random_span() for _ in range(50)]}
    resp = load_client.post("/v1/metrics/record-batch", json=payload)
    assert resp.status_code == 200
    assert resp.json()["recorded_count"] == 50


@pytest.mark.performance
def test_load_10_batches_of_50(load_client):
    total_recorded = 0
    for _ in range(10):
        payload = {"spans": [_random_span() for _ in range(50)]}
        resp = load_client.post("/v1/metrics/record-batch", json=payload)
        assert resp.status_code == 200
        total_recorded += resp.json()["recorded_count"]
    assert total_recorded == 500


@pytest.mark.performance
def test_load_mixed_error_ratio(load_client):
    errors = 0
    success = 0
    for _ in range(100):
        span = _random_span()
        resp = load_client.post("/v1/metrics/record", json=span)
        assert resp.status_code == 200
        if span["status"] == "error":
            errors += 1
        else:
            success += 1
    assert success > 0
    assert errors >= 0


@pytest.mark.performance
def test_load_pii_and_injection_flags(load_client):
    pii_spans = []
    for _ in range(50):
        span = _random_span()
        span["pii_detected"] = True
        span["injection_attempt"] = True
        pii_spans.append(span)

    payload = {"spans": pii_spans}
    resp = load_client.post("/v1/metrics/record-batch", json=payload)
    assert resp.status_code == 200
    assert resp.json()["recorded_count"] == 50


@pytest.mark.performance
def test_load_all_models_covered(load_client):
    for model_entry in _MODELS:
        span = _random_span()
        span["model"] = model_entry["model"]
        span["provider"] = model_entry["provider"]
        resp = load_client.post("/v1/metrics/record", json=span)
        assert resp.status_code == 200
        assert resp.json()["recorded"] is True


@pytest.mark.performance
def test_load_high_token_counts(load_client):
    payload = {
        "spans": [
            {
                "model": "gpt-4o",
                "provider": "openai",
                "service_name": "heavy-svc",
                "prompt_tokens": 32000,
                "completion_tokens": 4096,
                "latency_ms_total": 10000,
                "status": "success",
            }
            for _ in range(20)
        ]
    }
    resp = load_client.post("/v1/metrics/record-batch", json=payload)
    assert resp.status_code == 200
    assert resp.json()["recorded_count"] == 20
