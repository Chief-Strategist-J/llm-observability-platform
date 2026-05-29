from __future__ import annotations

import pytest

from features.score_toxicity.service import score_toxicity
from features.score_toxicity.types import ToxicityInput, ToxicityScores

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

def test_score_toxicity_short_text():
    token_ids = list(range(100))
    scores = ToxicityScores(
        toxicity=0.1,
        severe_toxicity=0.01,
        obscene=0.02,
        threat=0.01,
        insult=0.03,
        identity_hate=0.01,
    )
    scorer = FakeToxicityScorer(token_ids, scores)
    publisher = FakeToxicityPublisher()

    result = score_toxicity(
        input=ToxicityInput(response_text="Hello world"),
        scorer=scorer,
        publisher=publisher,
        trace_id="t1",
        span_id="s1",
    )

    assert result.skipped is False
    assert result.score == 0.1
    assert result.flagged is False
    assert result.flag is None
    assert len(scorer.score_calls) == 1
    assert scorer.score_calls[0] == token_ids
    assert len(publisher.publish_calls) == 0

def test_score_toxicity_long_text_dual_pass():
    token_ids = list(range(600))
    scores = ToxicityScores(
        toxicity=0.6,
        severe_toxicity=0.01,
        obscene=0.02,
        threat=0.01,
        insult=0.03,
        identity_hate=0.01,
    )
    scorer = FakeToxicityScorer(token_ids, scores)
    publisher = FakeToxicityPublisher()

    result = score_toxicity(
        input=ToxicityInput(response_text="a" * 1000),
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
    assert scorer.score_calls[0] == list(range(510))
    assert scorer.score_calls[1] == list(range(90, 600))
    assert len(publisher.publish_calls) == 1
    assert publisher.publish_calls[0]["trace_id"] == "t1"
    assert publisher.publish_calls[0]["span_id"] == "s1"
    assert publisher.publish_calls[0]["score"] == 0.6

def test_score_toxicity_failure():
    class BrokenScorer:
        def tokenize(self, text: str) -> list[int]:
            raise ValueError("Tokenize failed")
        def score_token_ids(self, token_ids: list[int]) -> ToxicityScores:
            raise ValueError("Score failed")

    publisher = FakeToxicityPublisher()
    result = score_toxicity(
        input=ToxicityInput(response_text="fail"),
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
