from __future__ import annotations

import pytest

from core.domain.service import score_toxicity
from core.domain.types import ToxicityInput, ToxicityScores


class FakeToxicityScorer:
    def __init__(self, token_ids: list[int], scores: ToxicityScores) -> None:
        self._token_ids = token_ids
        self._scores = scores
        self.tokenize_calls: list[str] = []
        self.score_calls: list[list[int]] = []

    def tokenize(self, text: str) -> list[int]:
        self.tokenize_calls.append(text)
        return self._token_ids

    def score_token_ids(self, token_ids: list[int]) -> ToxicityScores:
        self.score_calls.append(token_ids)
        return self._scores


class FakeToxicityPublisher:
    def __init__(self) -> None:
        self.publish_calls: list[dict] = []

    def publish_flagged(
        self, trace_id: str, span_id: str, score: float, scores: ToxicityScores
    ) -> None:
        self.publish_calls.append({
            "trace_id": trace_id,
            "span_id": span_id,
            "score": score,
            "scores": scores,
        })


# ── Short text — single pass ──────────────────────────────────────────────────

def test_score_short_text_no_publisher():
    """Worker mode: no publisher, not flagged."""
    token_ids = list(range(100))
    scores = ToxicityScores(toxicity=0.1, severe_toxicity=0.01, obscene=0.02,
                            threat=0.01, insult=0.03, identity_hate=0.01)
    scorer = FakeToxicityScorer(token_ids, scores)

    result = score_toxicity(
        input=ToxicityInput(text="Hello world"),
        scorer=scorer,
        trace_id="12345678901234567890123456789012",
        span_id="1234567890123456",
    )

    assert result.long_response_strategy is None
    assert result.scores.toxicity == 0.1
    assert result.flagged is False
    assert result.skipped is False
    assert len(scorer.score_calls) == 1


def test_score_short_text_with_publisher_not_flagged():
    """Orchestrator mode: publisher wired, score below threshold — no event published."""
    token_ids = list(range(100))
    scores = ToxicityScores(toxicity=0.1, severe_toxicity=0.01, obscene=0.02,
                            threat=0.01, insult=0.03, identity_hate=0.01)
    scorer = FakeToxicityScorer(token_ids, scores)
    publisher = FakeToxicityPublisher()

    result = score_toxicity(
        input=ToxicityInput(text="Hello world"),
        scorer=scorer,
        publisher=publisher,
        trace_id="t1",
        span_id="s1",
    )

    assert result.skipped is False
    assert result.score == 0.1
    assert result.flagged is False
    assert result.flag is None
    assert len(publisher.publish_calls) == 0


# ── Long text — dual pass ─────────────────────────────────────────────────────

def test_score_long_text_dual_pass_strategy():
    """Worker mode: long text triggers dual-pass, strategy field set."""
    token_ids = list(range(600))
    scores = ToxicityScores(toxicity=0.6, severe_toxicity=0.01, obscene=0.02,
                            threat=0.01, insult=0.03, identity_hate=0.01)
    scorer = FakeToxicityScorer(token_ids, scores)

    result = score_toxicity(
        input=ToxicityInput(text="a" * 1000),
        scorer=scorer,
        trace_id="12345678901234567890123456789012",
        span_id="1234567890123456",
    )

    assert result.long_response_strategy == "max_of_two_passes"
    assert result.scores.toxicity == 0.6
    assert len(scorer.score_calls) == 2
    assert scorer.score_calls[0] == list(range(510))
    assert scorer.score_calls[1] == list(range(90, 600))


def test_score_long_text_with_publisher_flagged():
    """Orchestrator mode: long text, high toxicity — Kafka event published."""
    token_ids = list(range(600))
    scores = ToxicityScores(toxicity=0.6, severe_toxicity=0.01, obscene=0.02,
                            threat=0.01, insult=0.03, identity_hate=0.01)
    scorer = FakeToxicityScorer(token_ids, scores)
    publisher = FakeToxicityPublisher()

    result = score_toxicity(
        input=ToxicityInput(text="a" * 1000),
        scorer=scorer,
        publisher=publisher,
        trace_id="t1",
        span_id="s1",
    )

    assert result.skipped is False
    assert result.score == 0.6
    assert result.flagged is True
    assert result.flag == "TOXIC_RESPONSE"
    assert len(scorer.score_calls) == 2
    assert len(publisher.publish_calls) == 1
    assert publisher.publish_calls[0]["trace_id"] == "t1"
    assert publisher.publish_calls[0]["span_id"] == "s1"
    assert publisher.publish_calls[0]["score"] == 0.6


# ── Failure / skip ────────────────────────────────────────────────────────────

def test_score_failure_returns_skipped():
    """Any scorer exception should result in skipped=True, not a 500."""
    class BrokenScorer:
        def tokenize(self, text: str) -> list[int]:
            raise ValueError("Tokenize failed")
        def score_token_ids(self, token_ids: list[int]) -> ToxicityScores:
            raise ValueError("Score failed")

    publisher = FakeToxicityPublisher()
    result = score_toxicity(
        input=ToxicityInput(text="fail"),
        scorer=BrokenScorer(),
        publisher=publisher,
        trace_id="t1",
        span_id="s1",
    )

    assert result.skipped is True
    assert result.skip_reason == "pipeline_failure"
    assert result.score is None
    assert result.flagged is False
    assert result.flag is None
    assert len(publisher.publish_calls) == 0
