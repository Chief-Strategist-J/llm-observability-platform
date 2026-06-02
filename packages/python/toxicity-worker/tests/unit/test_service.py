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

    result = score_toxicity(
        input=ToxicityInput(text="Hello world"),
        scorer=scorer,
        trace_id="12345678901234567890123456789012",
        span_id="1234567890123456",
    )

    assert result.long_response_strategy is None
    assert result.scores.toxicity == 0.1
    assert len(scorer.score_calls) == 1
    assert scorer.score_calls[0] == token_ids

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
