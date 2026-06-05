from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

class FakeNliScorer:
    default_model_id = "fake/nli-deberta-v3-base"
    device_name = "cpu"

    def count_tokens(self, text: str, model_id: str | None = None) -> int:
        return len(text.split())

    def split_context_by_tokens(
        self,
        text: str,
        max_tokens: int = 400,
        model_id: str | None = None,
    ) -> list[str]:
        words = text.split()
        return [" ".join(words[i : i + max_tokens]) for i in range(0, len(words), max_tokens)]

    def score_pairs(
        self,
        pairs: list[tuple[str, str]],
        temperature: float = 1.5,
        batch_size: int | None = None,
        model_id: str | None = None,
    ) -> list[tuple[float, float, float]]:
        res = []
        for _, hyp in pairs:
            if "grounded" in hyp.lower():
                res.append((0.9, 0.05, 0.05))
            elif "hallucinate" in hyp.lower():
                res.append((0.05, 0.05, 0.9))
            else:
                res.append((0.1, 0.8, 0.1))
        return res

def _build_app():
    from fastapi import FastAPI
    from api.rest.v1.router import router as v1_router

    app = FastAPI()
    app.state.nli_scorer = FakeNliScorer()
    app.include_router(v1_router)
    return app

@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(_build_app())

def test_healthz_get(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["model"] == "fake/nli-deberta-v3-base"
    assert data["device"] == "cpu"

def test_healthz_post(client):
    resp = client.post("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["model"] == "fake/nli-deberta-v3-base"
    assert data["device"] == "cpu"

def test_score_nli_success(client):
    resp = client.post("/nli", json={
        "context": "This is a grounded paragraph context text.",
        "sentences": [
            "This is grounded.",
            "This will hallucinate.",
            "This is random."
        ],
        "temperature": 1.5
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 3
    
    r0 = data["results"][0]
    assert r0["sentence"] == "This is grounded."
    assert r0["label"] == "entailment"
    assert r0["probabilities"]["entailment"] > 0.8

    r1 = data["results"][1]
    assert r1["sentence"] == "This will hallucinate."
    assert r1["label"] == "contradiction"
    assert r1["probabilities"]["contradiction"] > 0.8

    assert abs(data["faithfulness_score"] - 0.3333) < 0.01
    assert data["flagged_sentences"] == ["This will hallucinate."]

def test_score_nli_with_custom_model(client):
    resp = client.post("/nli", json={
        "context": "Context",
        "sentences": ["This is grounded."],
        "model_id": "custom-model-repo"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["label"] == "entailment"

def test_score_nli_empty_sentences(client):
    resp = client.post("/nli", json={
        "context": "Context",
        "sentences": []
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["results"] == []
    assert data["faithfulness_score"] == 1.0
    assert data["flagged_sentences"] == []
