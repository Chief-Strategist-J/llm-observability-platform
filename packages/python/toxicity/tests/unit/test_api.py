from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from features.score_toxicity.types import ToxicityScores

class FakeToxicityScorer:
    model_id = "fake/toxicity-model"

    def tokenize(self, text: str) -> list[int]:
        return list(range(len(text.split())))

    def score_token_ids(self, token_ids: list[int]) -> ToxicityScores:
        return ToxicityScores(
            toxicity=0.1,
            severe_toxicity=0.01,
            obscene=0.02,
            threat=0.01,
            insult=0.03,
            identity_hate=0.01,
        )

class FakeToxicityPublisher:
    def publish_flagged(
        self, trace_id: str, span_id: str, score: float, scores: ToxicityScores
    ) -> None:
        pass

def _build_app():
    from fastapi import FastAPI
    from api.rest.v1.router import router as v1_router

    app = FastAPI()
    app.state.toxicity_scorer = FakeToxicityScorer()
    app.state.toxicity_publisher = FakeToxicityPublisher()
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
    assert data["model_id"] == "fake/toxicity-model"

def test_score_valid_returns_score(client):
    resp = client.post("/v1/score/toxicity", json={
        "trace_id": "t1",
        "span_id": "s1",
        "response_text": "This is a clean and polite sentence.",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["skipped"] is False
    assert data["score"] == 0.1
    assert data["flagged"] is False
    assert data["flag"] is None
    assert data["scores"]["toxicity"] == 0.1
    assert data["scores"]["severe_toxicity"] == 0.01
    assert data["scores"]["obscene"] == 0.02
    assert data["scores"]["threat"] == 0.01
    assert data["scores"]["insult"] == 0.03
    assert data["scores"]["identity_hate"] == 0.01

def test_score_response_has_trace_and_span_ids(client):
    resp = client.post("/v1/score/toxicity", json={
        "trace_id": "trace-123",
        "span_id": "span-456",
        "response_text": "Hello world",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["trace_id"] == "trace-123"
    assert data["span_id"] == "span-456"
