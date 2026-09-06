from __future__ import annotations
from handlers.span_quality.composite_scorer import compute_composite
from handlers.span_quality.types import ScoreMap


def test_all_scores_present():
    import pytest
    scores = ScoreMap(coherence=0.8, toxicity=0.1, faithfulness=0.9, perplexity=2.0)
    result, weights = compute_composite(scores)
    assert result is not None
    assert 0.0 <= result <= 1.0
    assert "perplexity" in weights
    assert weights["coherence"] == pytest.approx(0.25 / 0.85)
    assert weights["faithfulness"] == pytest.approx(0.35 / 0.85)
    assert weights["toxicity"] == pytest.approx(0.15 / 0.85)
    assert weights["perplexity"] == pytest.approx(0.10 / 0.85)


def test_no_scores_returns_none():
    scores = ScoreMap()
    result, weights = compute_composite(scores)
    assert result is None
    assert weights == {}


def test_only_toxicity_present():
    # toxicity inverted: 1 - 0.2 = 0.8, full weight to toxicity
    scores = ScoreMap(toxicity=0.2)
    result, weights = compute_composite(scores)
    assert result is not None
    assert abs(result - 0.8) < 0.0001
    assert weights == {"toxicity": 1.0}


def test_composite_clamped_to_zero_one():
    scores = ScoreMap(coherence=1.0, toxicity=0.0, faithfulness=1.0, perplexity=0.0)
    result, weights = compute_composite(scores)
    assert result is not None
    assert 0.0 <= result <= 1.0


def test_weights_renormalized_correctly():
    import pytest
    scores = ScoreMap(coherence=0.8, toxicity=0.1, faithfulness=0.8)
    result, weights = compute_composite(scores)
    assert weights["coherence"] == pytest.approx(0.25 / 0.75)
    assert weights["faithfulness"] == pytest.approx(0.35 / 0.75)
    assert weights["toxicity"] == pytest.approx(0.15 / 0.75)
