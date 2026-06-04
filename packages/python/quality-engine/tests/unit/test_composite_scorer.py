from __future__ import annotations
from handlers.span_quality.composite_scorer import compute_composite
from handlers.span_quality.types import ScoreMap


def test_all_scores_present():
    scores = ScoreMap(coherence=0.8, toxicity=0.1, faithfulness=0.9, perplexity=2.0)
    result = compute_composite(scores)
    assert result is not None
    assert 0.0 <= result <= 1.0


def test_no_scores_returns_none():
    scores = ScoreMap()
    assert compute_composite(scores) is None


def test_only_toxicity_present():
    # toxicity inverted: 1 - 0.2 = 0.8, full weight to toxicity
    scores = ScoreMap(toxicity=0.2)
    result = compute_composite(scores)
    assert result is not None
    assert abs(result - 0.8) < 0.0001


def test_composite_clamped_to_zero_one():
    scores = ScoreMap(coherence=1.0, toxicity=0.0, faithfulness=1.0, perplexity=0.0)
    result = compute_composite(scores)
    assert result is not None
    assert 0.0 <= result <= 1.0


def test_high_perplexity_reduces_composite():
    low_perp  = ScoreMap(coherence=0.8, toxicity=0.1, faithfulness=0.8, perplexity=1.0)
    high_perp = ScoreMap(coherence=0.8, toxicity=0.1, faithfulness=0.8, perplexity=100.0)
    assert compute_composite(low_perp) > compute_composite(high_perp)  # type: ignore[operator]
