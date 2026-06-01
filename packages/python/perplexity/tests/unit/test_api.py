from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SKIP_CONSOLE_EXPORTER", "true")
os.environ.setdefault("SKIP_OTLP_EXPORTER", "true")


class FakeLogprobsScorer:
    def compute(self, token_logprobs, response_text):
        if token_logprobs:
            import math
            n = len(token_logprobs)
            return math.exp(-sum(token_logprobs) / n)
        return None


class FakeGpt2Scorer:
    def is_available(self) -> bool:
        return True

    def compute(self, response_text: str) -> float:
        return 18.0


@pytest.fixture()
def client():
    from api.rest.v1.app import create_app
    app = create_app()
    app.state.logprobs_scorer = FakeLogprobsScorer()
    app.state.gpt2_scorer = FakeGpt2Scorer()
    return TestClient(app)


def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "scorer" in data


def test_score_with_token_logprobs_returns_200(client):
    payload = {
        "trace_id": "abc123",
        "span_id": "def456",
        "response_text": "The sky is blue and the grass is green.",
        "completion_tokens": 20,
        "prompt_type": "chat",
        "token_logprobs": [-2.0, -1.5, -2.5, -1.8],
    }
    resp = client.post("/v1/score/perplexity", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["skipped"] is False
    assert data["perplexity"] is not None
    assert data["score"] is not None
    assert data["weight"] == pytest.approx(0.10)
    assert data["scorer_used"] == "provider_logprobs"
    assert data["trace_id"] == "abc123"
    assert data["span_id"] == "def456"


def test_score_fallback_gpt2_when_no_logprobs(client):
    payload = {
        "trace_id": "aaa",
        "span_id": "bbb",
        "response_text": "Some output from the model.",
        "completion_tokens": 15,
        "prompt_type": "code",
    }
    resp = client.post("/v1/score/perplexity", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["skipped"] is False
    assert data["scorer_used"] == "gpt2_onnx"
    assert data["perplexity"] == pytest.approx(18.0)


def test_score_skip_completion_tokens_too_few(client):
    payload = {
        "trace_id": "t1",
        "span_id": "s1",
        "response_text": "short",
        "completion_tokens": 5,
        "prompt_type": "chat",
    }
    resp = client.post("/v1/score/perplexity", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["skipped"] is True
    assert data["skip_reason"] == "completion_tokens_too_few"
    assert data["perplexity"] is None
    assert data["score"] is None
    assert data["weight"] == pytest.approx(0.0)


def test_score_skip_content_filter(client):
    payload = {
        "trace_id": "t2",
        "span_id": "s2",
        "response_text": "some output",
        "completion_tokens": 20,
        "prompt_type": "rag",
        "finish_reason": "content_filter",
    }
    resp = client.post("/v1/score/perplexity", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["skipped"] is True
    assert data["skip_reason"] == "finish_reason_blocked"


def test_score_high_perplexity_flag(client):
    class HighPerplexityLogprobs:
        def compute(self, token_logprobs, response_text):
            return 300.0

    from api.rest.v1.app import create_app
    app = create_app()
    app.state.logprobs_scorer = HighPerplexityLogprobs()
    app.state.gpt2_scorer = FakeGpt2Scorer()
    c = TestClient(app)
    payload = {
        "trace_id": "t3",
        "span_id": "s3",
        "response_text": "something very confusing",
        "completion_tokens": 20,
        "prompt_type": "chat",
        "token_logprobs": [-5.0],
    }
    resp = c.post("/v1/score/perplexity", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["high_perplexity_flag"] is True


def test_missing_required_field_returns_422(client):
    payload = {
        "trace_id": "t",
        "span_id": "s",
        "completion_tokens": 20,
    }
    resp = client.post("/v1/score/perplexity", json=payload)
    assert resp.status_code == 422


def test_prompt_type_preserved_in_response(client):
    payload = {
        "trace_id": "tx",
        "span_id": "sx",
        "response_text": "result output",
        "completion_tokens": 15,
        "prompt_type": "classification",
    }
    resp = client.post("/v1/score/perplexity", json=payload)
    assert resp.status_code == 200
    assert resp.json()["prompt_type"] == "classification"
