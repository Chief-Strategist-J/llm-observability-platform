from __future__ import annotations

import os
import pytest
import httpx
import pytest_asyncio

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


def _build_app(scorer=None):
    os.environ["SKIP_OTLP_EXPORTER"] = "true"
    os.environ["SKIP_CONSOLE_EXPORTER"] = "true"
    from api.rest.v1.app import create_app
    app = create_app()
    app.state.toxicity_scorer = scorer or FakeToxicityScorer()
    app.state.toxicity_publisher = None
    return app


@pytest_asyncio.fixture(scope="module")
async def client():
    app = _build_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c


# ── Health ───────────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_healthz_get(client):
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["model_id"] == "fake/toxicity-model"


@pytest.mark.anyio
async def test_healthz_post(client):
    resp = await client.post("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── Score — basic ─────────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_score_returns_all_labels(client):
    resp = await client.post("/score", json={"text": "This is a clean sentence."})
    assert resp.status_code == 200
    data = resp.json()
    assert data["toxicity"] == 0.15
    assert data["severe_toxicity"] == 0.01
    assert data["obscene"] == 0.02
    assert data["threat"] == 0.01
    assert data["insult"] == 0.03
    assert data["identity_hate"] == 0.01


@pytest.mark.anyio
async def test_score_not_flagged_below_threshold(client):
    resp = await client.post("/score", json={"text": "Hello world"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["flagged"] is False
    assert data.get("flag") is None  # excluded from response when None (response_model_exclude_none)


# ── Score — long text ─────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_score_long_text_returns_strategy(client):
    resp = await client.post("/score", json={"text": "word " * 600})
    assert resp.status_code == 200
    data = resp.json()
    assert data["toxicity"] == 0.15
    assert data["long_response_strategy"] == "max_of_two_passes"


# ── Score — trace context ─────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_score_accepts_trace_id_in_body(client):
    resp = await client.post("/score", json={
        "text": "testing trace context",
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
        "span_id": "00f067aa0ba902b7",
    })
    assert resp.status_code == 200
    assert resp.json()["toxicity"] == 0.15


@pytest.mark.anyio
async def test_score_accepts_traceparent_header(client):
    resp = await client.post(
        "/score",
        json={"text": "testing traceparent header"},
        headers={"traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"},
    )
    assert resp.status_code == 200
    assert resp.json()["toxicity"] == 0.15


# ── Score — skipped ───────────────────────────────────────────────────────────

@pytest.mark.anyio
async def test_score_skipped_on_broken_scorer():
    class BrokenScorer:
        model_id = "broken/model"
        def tokenize(self, text: str) -> list[int]:
            raise RuntimeError("broken")
        def score_token_ids(self, token_ids: list[int]) -> ToxicityScores:
            raise RuntimeError("broken")

    broken_app = _build_app(scorer=BrokenScorer())
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=broken_app),
        base_url="http://testserver",
    ) as broken_client:
        resp = await broken_client.post("/score", json={"text": "will fail"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["skipped"] is True
    assert data["skip_reason"] == "pipeline_failure"
