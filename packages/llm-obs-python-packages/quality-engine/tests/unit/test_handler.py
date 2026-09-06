from __future__ import annotations
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from handlers.span_quality.handler import SpanQualityHandler, _check_skip
from handlers.span_quality.types import SampledSpan, ScoreMap


def _make_raw(
    span_id: str = "s1",
    finish_reason: str = "stop",
    completion_tokens: int = 50,
    **kwargs,
) -> bytes:
    payload = {
        "span_id": span_id,
        "trace_id": "t1",
        "model": "gpt-4",
        "endpoint": "/v1/chat",
        "prompt_text": "What is 2+2?",
        "response_text": "The answer is 4. This is a reasonably detailed response.",
        "completion_tokens": completion_tokens,
        "finish_reason": finish_reason,
        "scored_at": "2026-06-04T12:00:00+00:00",
    }
    payload.update(kwargs)
    return json.dumps(payload).encode()


def _make_handler():
    repo     = MagicMock()
    cache    = MagicMock()
    temporal = AsyncMock()
    embedder = AsyncMock()
    producer = MagicMock()

    repo.get_window_avg.return_value = None
    cache.get_baseline.return_value = None
    cache.is_alert_rate_limited.return_value = False
    temporal.trigger_quality_score_workflow.return_value = "wf-id-123"
    embedder.embed.return_value = None

    return SpanQualityHandler(
        repo=repo, cache=cache, temporal=temporal,
        embedding_client=embedder, producer=producer,
    ), repo, cache, temporal, embedder, producer


# ── F-Q-01 pre-flight skip checks ─────────────────────────────────────────

def test_skip_content_filter():
    span = SampledSpan(
        span_id="s1", trace_id="t1", model="m", endpoint="e",
        prompt_text="x", response_text="x", completion_tokens=50,
        finish_reason="content_filter",
    )
    assert _check_skip(span) == "finish_reason:content_filter"


def test_skip_low_completion_tokens():
    span = SampledSpan(
        span_id="s1", trace_id="t1", model="m", endpoint="e",
        prompt_text="x", response_text="x", completion_tokens=5,
        finish_reason="stop",
    )
    assert _check_skip(span) is not None


def test_no_skip_normal_span():
    span = SampledSpan(
        span_id="s1", trace_id="t1", model="m", endpoint="e",
        prompt_text="x", response_text="x", completion_tokens=50,
        finish_reason="stop",
    )
    assert _check_skip(span) is None


# ── F-Q-01 skipped row written for content_filter ─────────────────────────

@pytest.mark.asyncio
async def test_handler_writes_skipped_row_for_content_filter():
    handler, repo, *_ = _make_handler()
    await handler.handle(_make_raw(finish_reason="content_filter"), headers={})
    repo.insert_score.assert_called_once()
    call_args = repo.insert_score.call_args[0][0]
    assert call_args.skipped_reason == "finish_reason:content_filter"
    assert call_args.composite_score is None


# ── F-Q-01 Temporal triggered for normal span ─────────────────────────────

@pytest.mark.asyncio
async def test_handler_triggers_temporal_for_valid_span():
    handler, repo, cache, temporal, embedder, producer = _make_handler()
    await handler.handle(_make_raw(), headers={})
    temporal.trigger_quality_score_workflow.assert_awaited_once()


# ── F-Q-07 + F-Q-08 via handle_score_result ───────────────────────────────

@pytest.mark.asyncio
async def test_handle_score_result_updates_baseline():
    handler, repo, cache, *_ = _make_handler()
    cache.get_baseline.return_value = 0.80
    await handler.handle_score_result(
        span_id="s1", model="gpt-4", endpoint="/v1/chat",
        prompt_type="chat", response_language="en",
        scores=ScoreMap(coherence=0.9, toxicity=0.05),
        quality_flags=[],
        scored_at=datetime.now(timezone.utc),
        trace_id="t1",
    )
    cache.set_baseline.assert_called_once()


@pytest.mark.asyncio
async def test_handle_score_result_emits_toxicity_flag():
    handler, repo, cache, temporal, embedder, producer = _make_handler()
    await handler.handle_score_result(
        span_id="s1", model="gpt-4", endpoint="/v1/chat",
        prompt_type="chat", response_language="en",
        scores=ScoreMap(toxicity=0.60),  # above 0.50 threshold
        quality_flags=[],
        scored_at=datetime.now(timezone.utc),
        trace_id="t1",
        user_id="user-123",
    )
    producer.produce.assert_called()
    call_args = producer.produce.call_args
    assert call_args[1]["topic"] == "llm.toxicity.flagged"
    payload = json.loads(call_args[1]["value"].decode())
    assert payload["user_id"] == "user-123"
    assert payload["toxicity_score"] == 0.60

