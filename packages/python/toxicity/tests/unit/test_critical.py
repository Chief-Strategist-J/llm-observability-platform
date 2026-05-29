from __future__ import annotations

import pytest

from features.score_toxicity.service import score_toxicity
from features.score_toxicity.types import ToxicityInput, ToxicityScores

class _NliRecorder:
    def __init__(self, responses: list[ToxicityScores]) -> None:
        self._responses = iter(responses)
        self.calls: list[list[int]] = []

    def tokenize(self, text: str) -> list[int]:
        return list(range(len(text.split())))

    def score_token_ids(self, token_ids: list[int]) -> ToxicityScores:
        self.calls.append(list(token_ids))
        return next(self._responses)

class _StaticScorer:
    def __init__(self, token_ids: list[int], scores: ToxicityScores) -> None:
        self._token_ids = token_ids
        self._scores = scores
        self.calls: list[list[int]] = []

    def tokenize(self, text: str) -> list[int]:
        return self._token_ids

    def score_token_ids(self, token_ids: list[int]) -> ToxicityScores:
        self.calls.append(list(token_ids))
        return self._scores

class _MockPublisher:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def publish_flagged(
        self, trace_id: str, span_id: str, score: float, scores: ToxicityScores
    ) -> None:
        self.calls.append({
            "trace_id": trace_id,
            "span_id": span_id,
            "score": score,
            "scores": scores,
        })

class TestTokenSplitting:
    def test_short_response_no_split(self):
        token_ids = list(range(500))
        scores = ToxicityScores(0.1, 0.01, 0.02, 0.01, 0.03, 0.01)
        scorer = _StaticScorer(token_ids, scores)
        publisher = _MockPublisher()

        result = score_toxicity(
            input=ToxicityInput("Hello"),
            scorer=scorer,
            publisher=publisher,
        )

        assert result.skipped is False
        assert len(scorer.calls) == 1
        assert len(scorer.calls[0]) == 500

    def test_boundary_exactly_510_no_split(self):
        token_ids = list(range(510))
        scores = ToxicityScores(0.1, 0.01, 0.02, 0.01, 0.03, 0.01)
        scorer = _StaticScorer(token_ids, scores)
        publisher = _MockPublisher()

        result = score_toxicity(
            input=ToxicityInput("Hello"),
            scorer=scorer,
            publisher=publisher,
        )

        assert result.skipped is False
        assert len(scorer.calls) == 1
        assert len(scorer.calls[0]) == 510

    def test_long_response_split_first_last_510(self):
        token_ids = list(range(600))
        scores_first = ToxicityScores(0.4, 0.01, 0.02, 0.01, 0.03, 0.01)
        scores_last = ToxicityScores(0.6, 0.05, 0.01, 0.02, 0.01, 0.03)
        scorer = _NliRecorder([scores_first, scores_last])
        publisher = _MockPublisher()

        class CustomScorer:
            def tokenize(self, text: str) -> list[int]:
                return token_ids
            def score_token_ids(self, ids: list[int]) -> ToxicityScores:
                return scorer.score_token_ids(ids)

        result = score_toxicity(
            input=ToxicityInput("Hello"),
            scorer=CustomScorer(),
            publisher=publisher,
        )

        assert result.skipped is False
        assert len(scorer.calls) == 2
        assert scorer.calls[0] == list(range(510))
        assert scorer.calls[1] == list(range(90, 600))
        assert result.scores.toxicity == 0.6
        assert result.scores.severe_toxicity == 0.05
        assert result.scores.obscene == 0.02
        assert result.scores.threat == 0.02
        assert result.scores.insult == 0.03
        assert result.scores.identity_hate == 0.03

class TestToxicityThreshold:
    def test_threshold_below(self):
        scores = ToxicityScores(0.49, 0.0, 0.0, 0.0, 0.0, 0.0)
        scorer = _StaticScorer(list(range(10)), scores)
        publisher = _MockPublisher()

        result = score_toxicity(ToxicityInput("text"), scorer, publisher)
        assert result.flagged is False
        assert result.flag is None
        assert len(publisher.calls) == 0

    def test_threshold_exactly_border_below(self):
        scores = ToxicityScores(0.50, 0.0, 0.0, 0.0, 0.0, 0.0)
        scorer = _StaticScorer(list(range(10)), scores)
        publisher = _MockPublisher()

        result = score_toxicity(ToxicityInput("text"), scorer, publisher)
        assert result.flagged is False
        assert result.flag is None

    def test_threshold_above(self):
        scores = ToxicityScores(0.51, 0.0, 0.0, 0.0, 0.0, 0.0)
        scorer = _StaticScorer(list(range(10)), scores)
        publisher = _MockPublisher()

        result = score_toxicity(ToxicityInput("text"), scorer, publisher)
        assert result.flagged is True
        assert result.flag == "TOXIC_RESPONSE"
        assert len(publisher.calls) == 1

class TestPublisherCall:
    def test_publisher_called_with_ids(self):
        scores = ToxicityScores(0.9, 0.0, 0.0, 0.0, 0.0, 0.0)
        scorer = _StaticScorer(list(range(10)), scores)
        publisher = _MockPublisher()

        score_toxicity(ToxicityInput("text"), scorer, publisher, trace_id="trace1", span_id="span1")
        assert len(publisher.calls) == 1
        assert publisher.calls[0]["trace_id"] == "trace1"
        assert publisher.calls[0]["span_id"] == "span1"
        assert publisher.calls[0]["score"] == 0.9

class TestOTelTracing:
    def test_trace_span_with_ids(self):
        scores = ToxicityScores(0.1, 0.0, 0.0, 0.0, 0.0, 0.0)
        scorer = _StaticScorer(list(range(10)), scores)
        publisher = _MockPublisher()

        result = score_toxicity(
            ToxicityInput("text"),
            scorer,
            publisher,
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            span_id="00f067aa0ba902b7",
        )
        assert result.score == 0.1
