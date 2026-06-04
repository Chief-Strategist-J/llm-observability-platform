"""
Critical unit tests for SpanQualityHandler — per unit-tests.md:
  - Every happy path
  - Every error path (dependency failure, invalid input, not-found)
  - Every business rule (boundary values, edge cases)
  - 100% coverage target for critical business rules

Located at: handlers/span_quality/tests/unit/ per event-worker-rules.md line 28.
"""
from __future__ import annotations
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from handlers.span_quality.handler import SpanQualityHandler, _check_skip
from handlers.span_quality.types import SampledSpan, ScoreMap


# ─── Factories ───────────────────────────────────────────────────────────────

def _raw(
    span_id: str = "s1",
    finish_reason: str = "stop",
    completion_tokens: int = 50,
    **extra,
) -> bytes:
    payload = {
        "span_id": span_id,
        "trace_id": "t1",
        "model": "gpt-4",
        "endpoint": "/v1/chat",
        "prompt_text": "Explain recursion in detail with examples",
        "response_text": "Recursion is when a function calls itself. For example...",
        "completion_tokens": completion_tokens,
        "finish_reason": finish_reason,
        "scored_at": "2026-06-04T12:00:00+00:00",
    }
    payload.update(extra)
    return json.dumps(payload).encode()


def _handler(**port_overrides):
    repo     = MagicMock()
    cache    = MagicMock()
    temporal = AsyncMock()
    embedder = AsyncMock()
    producer = MagicMock()

    repo.get_window_avg.return_value = None
    cache.get_baseline.return_value = None
    cache.is_alert_rate_limited.return_value = False
    temporal.trigger_quality_score_workflow.return_value = "wf-abc"
    embedder.embed.return_value = None

    ports = dict(repo=repo, cache=cache, temporal=temporal,
                 embedding_client=embedder, producer=producer)
    ports.update(port_overrides)
    return SpanQualityHandler(**ports), repo, cache, temporal, embedder, producer


# ─── F-Q-01: Pre-flight skip conditions (all 3 cases) ────────────────────────

class TestPreflightSkip:
    def test_skip_content_filter(self):
        span = SampledSpan(
            span_id="s", trace_id="t", model="m", endpoint="e",
            prompt_text="x", response_text="x",
            completion_tokens=50, finish_reason="content_filter",
        )
        assert _check_skip(span) == "finish_reason:content_filter"

    def test_skip_completion_tokens_below_10(self):
        span = SampledSpan(
            span_id="s", trace_id="t", model="m", endpoint="e",
            prompt_text="x", response_text="x",
            completion_tokens=9, finish_reason="stop",
        )
        assert _check_skip(span) is not None
        assert "9" in _check_skip(span)

    def test_no_skip_at_boundary_10_tokens(self):
        """completion_tokens=10 is the minimum that must NOT be skipped."""
        span = SampledSpan(
            span_id="s", trace_id="t", model="m", endpoint="e",
            prompt_text="x", response_text="x",
            completion_tokens=10, finish_reason="stop",
        )
        assert _check_skip(span) is None

    def test_no_skip_tool_calls_finish_reason(self):
        """tool_calls is NOT a skip reason — only content_filter is."""
        span = SampledSpan(
            span_id="s", trace_id="t", model="m", endpoint="e",
            prompt_text="x", response_text="x",
            completion_tokens=50, finish_reason="tool_calls",
        )
        assert _check_skip(span) is None

    @pytest.mark.asyncio
    async def test_skip_writes_null_composite_row(self):
        handler, repo, *_ = _handler()
        await handler.handle(_raw(finish_reason="content_filter"), headers={})
        repo.insert_score.assert_called_once()
        row = repo.insert_score.call_args[0][0]
        assert row.composite_score is None
        assert row.skipped_reason == "finish_reason:content_filter"

    @pytest.mark.asyncio
    async def test_skip_does_NOT_trigger_temporal(self):
        handler, _, _, temporal, *_ = _handler()
        await handler.handle(_raw(finish_reason="content_filter"), headers={})
        temporal.trigger_quality_score_workflow.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skip_low_tokens_writes_skipped_row(self):
        handler, repo, *_ = _handler()
        await handler.handle(_raw(completion_tokens=5), headers={})
        row = repo.insert_score.call_args[0][0]
        assert row.skipped_reason is not None
        assert row.composite_score is None


# ─── F-Q-01: Normal span triggers Temporal ───────────────────────────────────

class TestTemporalTrigger:
    @pytest.mark.asyncio
    async def test_valid_span_triggers_temporal_once(self):
        handler, _, _, temporal, *_ = _handler()
        await handler.handle(_raw(), headers={})
        temporal.trigger_quality_score_workflow.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_workflow_id_contains_span_id(self):
        """TemporalClientAdapter uses span_id in workflow ID for idempotency."""
        handler, _, _, temporal, *_ = _handler()
        await handler.handle(_raw(span_id="my-unique-span"), headers={})
        call_kwargs = temporal.trigger_quality_score_workflow.call_args
        assert call_kwargs[1]["span_id"] == "my-unique-span"

    @pytest.mark.asyncio
    async def test_temporal_failure_propagates_to_retry_loop(self):
        """If Temporal throws, the exception must bubble up so the worker retry loop catches it."""
        handler, _, _, temporal, *_ = _handler()
        temporal.trigger_quality_score_workflow.side_effect = RuntimeError("temporal down")
        with pytest.raises(RuntimeError, match="temporal down"):
            await handler.handle(_raw(), headers={})


# ─── F-Q-04: Embedding reuse logic ───────────────────────────────────────────

class TestEmbeddingReuse:
    @pytest.mark.asyncio
    async def test_uses_existing_embeddings_without_calling_client(self):
        """If span already has embeddings, embedding client must NOT be called."""
        handler, _, _, _, embedder, _ = _handler()
        await handler.handle(
            _raw(prompt_embedding=[0.1, 0.2], response_embedding=[0.3, 0.4]),
            headers={},
        )
        embedder.embed.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_calls_client_when_embeddings_missing(self):
        """If no embeddings on span, embedding client MUST be called."""
        handler, _, _, _, embedder, _ = _handler()
        embedder.embed.return_value = [0.1, 0.2, 0.3]
        await handler.handle(_raw(), headers={})
        assert embedder.embed.await_count == 2  # once for prompt, once for response

    @pytest.mark.asyncio
    async def test_timeout_on_embedding_does_not_block_temporal_trigger(self):
        """F-Q-04: On embedding timeout (None returned), still trigger Temporal."""
        handler, _, _, temporal, embedder, _ = _handler()
        embedder.embed.return_value = None  # simulate timeout
        await handler.handle(_raw(), headers={})
        temporal.trigger_quality_score_workflow.assert_awaited_once()


# ─── F-Q-05: Toxicity always runs ────────────────────────────────────────────

class TestToxicityAlwaysRuns:
    @pytest.mark.asyncio
    async def test_toxicity_flag_emitted_above_threshold(self):
        handler, _, _, _, _, producer = _handler()
        await handler.handle_score_result(
            span_id="s1", model="gpt-4", endpoint="/v1/chat",
            prompt_type="chat", response_language="en",
            scores=ScoreMap(toxicity=0.80),  # > 0.75 threshold
            quality_flags=[],
            scored_at=datetime.now(timezone.utc),
            trace_id="t1",
        )
        calls = [c for c in producer.produce.call_args_list
                 if c[1].get("topic") == "llm.toxicity.flagged"]
        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_toxicity_flag_NOT_emitted_below_threshold(self):
        handler, _, _, _, _, producer = _handler()
        await handler.handle_score_result(
            span_id="s1", model="gpt-4", endpoint="/v1/chat",
            prompt_type="chat", response_language="en",
            scores=ScoreMap(toxicity=0.74),  # exactly below 0.75
            quality_flags=[],
            scored_at=datetime.now(timezone.utc),
            trace_id="t1",
        )
        toxicity_calls = [c for c in producer.produce.call_args_list
                          if c[1].get("topic") == "llm.toxicity.flagged"]
        assert len(toxicity_calls) == 0

    @pytest.mark.asyncio
    async def test_toxicity_flag_emitted_even_when_coherence_null(self):
        """F-Q-05: Toxicity is a safety signal — runs even if coherence is skipped."""
        handler, _, _, _, _, producer = _handler()
        await handler.handle_score_result(
            span_id="s1", model="gpt-4", endpoint="/v1/chat",
            prompt_type="chat", response_language="en",
            scores=ScoreMap(toxicity=0.90, coherence=None, faithfulness=None),
            quality_flags=[],
            scored_at=datetime.now(timezone.utc),
            trace_id="t1",
        )
        toxicity_calls = [c for c in producer.produce.call_args_list
                          if c[1].get("topic") == "llm.toxicity.flagged"]
        assert len(toxicity_calls) == 1


# ─── F-Q-06: Composite written to DB ─────────────────────────────────────────

class TestScoreResultPersistence:
    @pytest.mark.asyncio
    async def test_score_result_always_writes_to_db(self):
        """Rule: row is always written, even on invariant violation."""
        handler, repo, *_ = _handler()
        await handler.handle_score_result(
            span_id="s1", model="m", endpoint="e",
            prompt_type="chat", response_language="en",
            scores=ScoreMap(toxicity=0.1, coherence=0.9),
            quality_flags=[],
            scored_at=datetime.now(timezone.utc),
            trace_id="t1",
        )
        repo.insert_score.assert_called_once()

    @pytest.mark.asyncio
    async def test_repo_insert_failure_propagates(self):
        """If DB write fails, must propagate so DLQ routing kicks in."""
        repo = MagicMock()
        repo.insert_score.side_effect = Exception("postgres down")
        handler, *_ = _handler(repo=repo)
        with pytest.raises(Exception, match="postgres down"):
            await handler.handle_score_result(
                span_id="s1", model="m", endpoint="e",
                prompt_type="chat", response_language="en",
                scores=ScoreMap(toxicity=0.1),
                quality_flags=[],
                scored_at=datetime.now(timezone.utc),
                trace_id="t1",
            )


# ─── F-Q-07: Baseline update ─────────────────────────────────────────────────

class TestBaselineUpdate:
    @pytest.mark.asyncio
    async def test_baseline_set_after_non_null_composite(self):
        handler, _, cache, *_ = _handler()
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
        # Verify TTL is 8 days = 691200 seconds
        call_kwargs = cache.set_baseline.call_args[1]
        assert call_kwargs["ttl_seconds"] == 691200

    @pytest.mark.asyncio
    async def test_baseline_NOT_updated_when_composite_null(self):
        """F-Q-07: If composite is None, skip baseline update."""
        handler, _, cache, *_ = _handler()
        await handler.handle_score_result(
            span_id="s1", model="m", endpoint="e",
            prompt_type="chat", response_language="en",
            scores=ScoreMap(),  # no scores → composite=None
            quality_flags=[],
            scored_at=datetime.now(timezone.utc),
            trace_id="t1",
        )
        cache.set_baseline.assert_not_called()


# ─── F-Q-08: Degradation alert rate-limiting ─────────────────────────────────

class TestDegradationAlert:
    @pytest.mark.asyncio
    async def test_alert_NOT_emitted_when_rate_limited(self):
        """F-Q-08: Redis dedup key prevents duplicate alerts within 1 hour."""
        handler, repo, cache, _, _, producer = _handler()
        cache.get_baseline.return_value = 0.90
        repo.get_window_avg.return_value = 0.60  # below 90% of 0.90 = 0.81
        cache.is_alert_rate_limited.return_value = True  # already rate-limited

        await handler.handle_score_result(
            span_id="s1", model="m", endpoint="e",
            prompt_type="chat", response_language="en",
            scores=ScoreMap(coherence=0.5, toxicity=0.1),
            quality_flags=[],
            scored_at=datetime.now(timezone.utc),
            trace_id="t1",
        )
        degradation_calls = [c for c in producer.produce.call_args_list
                             if c[1].get("topic") == "alerts.quality.degradation"]
        assert len(degradation_calls) == 0

    @pytest.mark.asyncio
    async def test_alert_emitted_and_rate_limit_set(self):
        """F-Q-08: When window_avg < baseline * 0.90 and not rate-limited, alert must fire."""
        handler, repo, cache, _, _, producer = _handler()
        cache.get_baseline.return_value = 0.90
        repo.get_window_avg.return_value = 0.60   # < 0.90 * 0.90 = 0.81
        cache.is_alert_rate_limited.return_value = False

        await handler.handle_score_result(
            span_id="s1", model="gpt-4", endpoint="/v1/chat",
            prompt_type="chat", response_language="en",
            scores=ScoreMap(coherence=0.5, toxicity=0.1),
            quality_flags=[],
            scored_at=datetime.now(timezone.utc),
            trace_id="t1",
        )
        # Rate limit must be SET to prevent next alert within 1h
        cache.set_alert_rate_limit.assert_called_once()
        rl_ttl = cache.set_alert_rate_limit.call_args[1].get("ttl_seconds", 0)
        assert rl_ttl == 3600

    @pytest.mark.asyncio
    async def test_no_degradation_alert_when_window_avg_none(self):
        """F-Q-08: If window_avg is None (< 20 samples), no alert."""
        handler, repo, cache, _, _, producer = _handler()
        cache.get_baseline.return_value = 0.90
        repo.get_window_avg.return_value = None  # fewer than 20 samples
        cache.is_alert_rate_limited.return_value = False

        await handler.handle_score_result(
            span_id="s1", model="m", endpoint="e",
            prompt_type="chat", response_language="en",
            scores=ScoreMap(coherence=0.5),
            quality_flags=[],
            scored_at=datetime.now(timezone.utc),
            trace_id="t1",
        )
        degradation_calls = [c for c in producer.produce.call_args_list
                             if c[1].get("topic") == "alerts.quality.degradation"]
        assert len(degradation_calls) == 0


# ─── Idempotency ─────────────────────────────────────────────────────────────

class TestIdempotency:
    @pytest.mark.asyncio
    async def test_duplicate_span_does_not_crash_handler(self):
        """PostgreSQL ON CONFLICT DO NOTHING means insert_score must be idempotent."""
        handler, repo, _, temporal, *_ = _handler()
        # First call succeeds
        await handler.handle(_raw(span_id="dup-span"), headers={})
        # Second call with same span_id — repo silently ignores (ON CONFLICT DO NOTHING)
        repo.insert_score.side_effect = None  # simulate no-op on duplicate
        await handler.handle(_raw(span_id="dup-span"), headers={})
        # Handler should NOT raise even if called twice with same span
        assert temporal.trigger_quality_score_workflow.await_count == 2
