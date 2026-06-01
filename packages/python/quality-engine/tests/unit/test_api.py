from __future__ import annotations

from fastapi.testclient import TestClient

from api.rest.v1.app import app

client = TestClient(app)

def test_health_check_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

def test_score_composite_endpoint_success():
    payload = {
        "trace_id": "api_trace_id",
        "span_id": "api_span_id",
        "coherence_score": 0.85,
        "faithfulness_score": 0.90,
        "toxicity_score": 0.05,
        "perplexity": 2.5,
        "perplexity_baseline": 2.0,
    }
    resp = client.post("/v1/score/composite", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["trace_id"] == "api_trace_id"
    assert data["span_id"] == "api_span_id"
    assert data["composite_score"] is not None
    assert data["quality_skipped_reason"] is None
    assert "coherence" in data["active_weights"]
    assert "coherence" in data["raw_contributions"]

def test_score_composite_endpoint_all_null():
    payload = {
        "trace_id": "api_trace_null",
        "span_id": "api_span_null",
        "coherence_score": None,
        "faithfulness_score": None,
        "toxicity_score": None,
        "perplexity": None,
    }
    resp = client.post("/v1/score/composite", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["trace_id"] == "api_trace_null"
    assert data["span_id"] == "api_span_null"
    assert data["composite_score"] is None
    assert data["quality_skipped_reason"] == "all_scores_null"

def test_score_composite_validation_error():
    payload = {
        "trace_id": "api_trace_invalid",
    }
    resp = client.post("/v1/score/composite", json=payload)
    assert resp.status_code == 422
