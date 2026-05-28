from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from api.rest.v1.router import router as v1_router
from infra.adapters.scorers.scorer_registry import ScorerRegistry


EMB_A = [1.0, 0.0, 0.0]
EMB_B = [0.0, 1.0, 0.0]
EMB_SAME = [1.0, 0.0, 0.0]


class ControlledScorer:
    def __init__(self, name: str, model_id: str, score: float) -> None:
        self._name = name
        self._model_id = model_id
        self._score = score

    @property
    def name(self) -> str:
        return self._name

    @property
    def model_id(self) -> str:
        return self._model_id

    def compute(self, prompt: list[float], response: list[float]) -> float:
        return self._score


class NullEmbeddingStore:
    def fetch_embeddings(self, trace_id: str, span_id: str) -> tuple[None, None]:
        return None, None


class FixedEmbeddingStore:
    def __init__(self, prompt: list[float], response: list[float]) -> None:
        self._prompt = prompt
        self._response = response

    def fetch_embeddings(
        self, trace_id: str, span_id: str
    ) -> tuple[list[float], list[float]]:
        return self._prompt, self._response


def _make_client(
    scorer: object,
    embedding_store: object,
    primary: str = "test",
) -> TestClient:
    app = FastAPI()
    registry = ScorerRegistry()
    registry.register(scorer)  # type: ignore[arg-type]
    app.state.scorer_registry = registry
    app.state.embedding_store = embedding_store
    app.state.primary_scorer_name = primary
    app.include_router(v1_router)
    return TestClient(app)


def test_api_score_ok_response_shape() -> None:
    scorer = ControlledScorer("test", "test/v1", 0.9)
    client = _make_client(scorer, NullEmbeddingStore())
    resp = client.post(
        "/v1/score/semantic-coherence",
        json={
            "trace_id": "t1",
            "span_id": "s1",
            "prompt_type": "chat",
            "pii_detected": False,
            "prompt_embedding": EMB_A,
            "response_embedding": EMB_A,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["trace_id"] == "t1"
    assert body["span_id"] == "s1"
    assert body["skipped"] is False
    assert body["skip_reason"] is None
    assert body["primary"]["scorer_name"] == "test"
    assert body["primary"]["score"] == pytest.approx(0.9)
    assert body["primary"]["label"] == "OK"
    assert len(body["all_scores"]) == 1


def test_api_pii_returns_skipped_null_score() -> None:
    scorer = ControlledScorer("test", "test/v1", 0.9)
    client = _make_client(scorer, NullEmbeddingStore())
    resp = client.post(
        "/v1/score/semantic-coherence",
        json={
            "trace_id": "t2",
            "span_id": "s2",
            "prompt_type": "rag",
            "pii_detected": True,
            "prompt_embedding": EMB_A,
            "response_embedding": EMB_A,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["skipped"] is True
    assert body["skip_reason"] == "pii_detected"
    assert body["primary"] is None
    assert body["all_scores"] == []


def test_api_missing_embeddings_fetched_from_store() -> None:
    scorer = ControlledScorer("test", "test/v1", 0.8)
    store = FixedEmbeddingStore(EMB_A, EMB_A)
    client = _make_client(scorer, store)
    resp = client.post(
        "/v1/score/semantic-coherence",
        json={
            "trace_id": "t3",
            "span_id": "s3",
            "prompt_type": "chat",
            "pii_detected": False,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["skipped"] is False
    assert body["primary"]["score"] == pytest.approx(0.8)


def test_api_missing_embeddings_store_also_null_returns_skipped() -> None:
    scorer = ControlledScorer("test", "test/v1", 0.8)
    client = _make_client(scorer, NullEmbeddingStore())
    resp = client.post(
        "/v1/score/semantic-coherence",
        json={
            "trace_id": "t4",
            "span_id": "s4",
            "prompt_type": "chat",
            "pii_detected": False,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["skipped"] is True
    assert body["skip_reason"] in (
        "prompt_embedding_null",
        "response_embedding_null",
    )


def test_api_unknown_scorer_name_returns_400() -> None:
    scorer = ControlledScorer("test", "test/v1", 0.8)
    client = _make_client(scorer, NullEmbeddingStore())
    resp = client.post(
        "/v1/score/semantic-coherence",
        json={
            "trace_id": "t5",
            "span_id": "s5",
            "prompt_type": "chat",
            "pii_detected": False,
            "prompt_embedding": EMB_A,
            "response_embedding": EMB_A,
            "scorers": ["does_not_exist"],
        },
    )
    assert resp.status_code == 400


def test_api_ensemble_runs_all_scorers_when_no_filter() -> None:
    s1 = ControlledScorer("scorer_a", "m/a", 0.9)
    s2 = ControlledScorer("scorer_b", "m/b", 0.2)
    app = FastAPI()
    registry = ScorerRegistry()
    registry.register(s1)
    registry.register(s2)
    app.state.scorer_registry = registry
    app.state.embedding_store = NullEmbeddingStore()
    app.state.primary_scorer_name = "scorer_a"
    app.include_router(v1_router)
    client = TestClient(app)
    resp = client.post(
        "/v1/score/semantic-coherence",
        json={
            "trace_id": "t6",
            "span_id": "s6",
            "prompt_type": "chat",
            "pii_detected": False,
            "prompt_embedding": EMB_A,
            "response_embedding": EMB_A,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    names = {s["scorer_name"] for s in body["all_scores"]}
    assert names == {"scorer_a", "scorer_b"}
    assert body["primary"]["scorer_name"] == "scorer_a"


def test_api_scorers_endpoint_lists_all() -> None:
    scorer = ControlledScorer("test", "test/model-v1", 0.5)
    client = _make_client(scorer, NullEmbeddingStore())
    resp = client.get("/v1/scorers")
    assert resp.status_code == 200
    body = resp.json()
    assert body["primary"] == "test"
    names = [s["name"] for s in body["scorers"]]
    assert "test" in names


def test_api_health_endpoint() -> None:
    scorer = ControlledScorer("test", "test/v1", 0.5)
    client = _make_client(scorer, NullEmbeddingStore())
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "test" in body["scorers"]


def test_api_select_specific_scorer_only() -> None:
    s1 = ControlledScorer("fast", "m/fast", 0.95)
    s2 = ControlledScorer("slow", "m/slow", 0.2)
    app = FastAPI()
    registry = ScorerRegistry()
    registry.register(s1)
    registry.register(s2)
    app.state.scorer_registry = registry
    app.state.embedding_store = NullEmbeddingStore()
    app.state.primary_scorer_name = "fast"
    app.include_router(v1_router)
    client = TestClient(app)
    resp = client.post(
        "/v1/score/semantic-coherence",
        json={
            "trace_id": "t7",
            "span_id": "s7",
            "prompt_type": "chat",
            "pii_detected": False,
            "prompt_embedding": EMB_A,
            "response_embedding": EMB_A,
            "scorers": ["fast"],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["all_scores"]) == 1
    assert body["all_scores"][0]["scorer_name"] == "fast"


def test_api_invalid_prompt_type_returns_422() -> None:
    scorer = ControlledScorer("test", "test/v1", 0.5)
    client = _make_client(scorer, NullEmbeddingStore())
    resp = client.post(
        "/v1/score/semantic-coherence",
        json={
            "trace_id": "t8",
            "span_id": "s8",
            "prompt_type": "not_a_valid_type",
            "pii_detected": False,
            "prompt_embedding": EMB_A,
            "response_embedding": EMB_A,
        },
    )
    assert resp.status_code == 422


def test_api_score_label_drives_from_threshold_not_hardcoded() -> None:
    scorer_above = ControlledScorer("above", "m/v1", 0.31)
    scorer_below = ControlledScorer("below", "m/v1", 0.29)

    app_above = FastAPI()
    reg_above = ScorerRegistry()
    reg_above.register(scorer_above)
    app_above.state.scorer_registry = reg_above
    app_above.state.embedding_store = NullEmbeddingStore()
    app_above.state.primary_scorer_name = "above"
    app_above.include_router(v1_router)
    client_above = TestClient(app_above)

    app_below = FastAPI()
    reg_below = ScorerRegistry()
    reg_below.register(scorer_below)
    app_below.state.scorer_registry = reg_below
    app_below.state.embedding_store = NullEmbeddingStore()
    app_below.state.primary_scorer_name = "below"
    app_below.include_router(v1_router)
    client_below = TestClient(app_below)

    payload = {
        "trace_id": "t9",
        "span_id": "s9",
        "prompt_type": "chat",
        "pii_detected": False,
        "prompt_embedding": EMB_A,
        "response_embedding": EMB_A,
    }
    assert client_above.post("/v1/score/semantic-coherence", json=payload).json()["primary"]["label"] == "OK"
    assert client_below.post("/v1/score/semantic-coherence", json=payload).json()["primary"]["label"] == "LOW_COHERENCE"
