from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from core.domain.types import ToxicityScores

class FakeToxicityScorer:
    model_id = "fake/toxicity-model"

    def tokenize(self, text: str) -> list[int]:
        return list(range(len(text.split())))

    def score_token_ids(self, token_ids: list[int]) -> ToxicityScores:
        return ToxicityScores(
            toxicity=0.15,
            severe_toxicity=0.01,
            obscene=0.02,
            threat=0.01,
            insult=0.03,
            identity_hate=0.01,
        )

def _build_app():
    from api.rest.v1.app import app
    app.state.toxicity_scorer = FakeToxicityScorer()
    return app

@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(_build_app())

def test_healthz_returns_200(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["model_id"] == "fake/toxicity-model"

def test_score_valid_returns_score(client):
    resp = client.post("/score", json={
        "text": "This is a clean and polite sentence.",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["toxicity"] == 0.15
    assert data["severe_toxicity"] == 0.01
    assert data["obscene"] == 0.02
    assert data["threat"] == 0.01
    assert data["insult"] == 0.03
    assert data["identity_hate"] == 0.01
    assert data["long_response_strategy"] == "single_pass"

def test_score_traceparent_header_context(client):
    resp = client.post(
        "/score",
        json={"text": "testing traceparent headers"},
        headers={"traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["toxicity"] == 0.15
