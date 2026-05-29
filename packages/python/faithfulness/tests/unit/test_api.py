from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class FakeSentencizer:
    def split(self, text: str, min_words: int) -> list[str]:
        return [s.strip() for s in text.split(".") if len(s.strip().split()) >= min_words]


class FakeNliScorer:
    model_id = "fake/nli-model"

    def score_pairs(self, pairs):
        return [(0.9, 0.05, 0.05)] * len(pairs)


def _make_client() -> TestClient:
    from api.rest.v1.app import create_app
    app = create_app.__wrapped__() if hasattr(create_app, "__wrapped__") else _build_app()
    return TestClient(app)


def _build_app():
    from fastapi import FastAPI
    from api.rest.v1.router import router as v1_router

    app = FastAPI()
    app.state.nli_scorer = FakeNliScorer()
    app.state.sentencizer = FakeSentencizer()
    app.include_router(v1_router)
    return app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(_build_app())


def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["model_id"] == "fake/nli-model"


def test_score_null_context_returns_skipped(client):
    resp = client.post("/v1/score/faithfulness", json={
        "trace_id": "t1",
        "span_id": "s1",
        "response_text": "The model said something.",
        "completion_tokens": 20,
        "rag_context": None,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["skipped"] is True
    assert data["skip_reason"] == "rag_context_null"
    assert data["score"] is None


def test_score_content_filter_returns_skipped(client):
    resp = client.post("/v1/score/faithfulness", json={
        "trace_id": "t1",
        "span_id": "s1",
        "response_text": "Some text.",
        "completion_tokens": 20,
        "rag_context": "x" * 60,
        "finish_reason": "content_filter",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["skipped"] is True
    assert data["skip_reason"] == "finish_reason_blocked"


def test_score_few_tokens_returns_skipped(client):
    resp = client.post("/v1/score/faithfulness", json={
        "trace_id": "t1",
        "span_id": "s1",
        "response_text": "The model output.",
        "completion_tokens": 5,
        "rag_context": "x" * 60,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["skipped"] is True
    assert data["skip_reason"] == "completion_tokens_too_few"


def test_score_valid_returns_score(client):
    resp = client.post("/v1/score/faithfulness", json={
        "trace_id": "t1",
        "span_id": "s1",
        "response_text": "The cat sat on the mat. The dog is happy. It was sunny outside.",
        "completion_tokens": 25,
        "rag_context": "x" * 60,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["skipped"] is False
    assert data["score"] is not None
    assert 0.0 <= data["score"] <= 1.0
    assert isinstance(data["sentence_results"], list)


def test_score_response_has_trace_and_span_ids(client):
    resp = client.post("/v1/score/faithfulness", json={
        "trace_id": "trace-abc",
        "span_id": "span-xyz",
        "response_text": "The cat sat on the mat. The dog ran.",
        "completion_tokens": 25,
        "rag_context": "x" * 60,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["trace_id"] == "trace-abc"
    assert data["span_id"] == "span-xyz"


def test_score_sentence_results_have_correct_shape(client):
    resp = client.post("/v1/score/faithfulness", json={
        "trace_id": "t1",
        "span_id": "s1",
        "response_text": "The cat sat on the mat. The dog ran away quickly.",
        "completion_tokens": 25,
        "rag_context": "x" * 60,
    })
    assert resp.status_code == 200
    results = resp.json()["sentence_results"]
    for item in results:
        assert "sentence" in item
        assert "label" in item
        assert "entailment_prob" in item
        assert 0.0 <= item["entailment_prob"] <= 1.0


def test_score_entailed_count_matches_sentence_results(client):
    resp = client.post("/v1/score/faithfulness", json={
        "trace_id": "t1",
        "span_id": "s1",
        "response_text": "The cat sat on the mat. The dog ran away quickly.",
        "completion_tokens": 25,
        "rag_context": "x" * 60,
    })
    assert resp.status_code == 200
    data = resp.json()
    counted = sum(1 for r in data["sentence_results"] if r["label"] == "entailment")
    assert data["entailed_count"] == counted
