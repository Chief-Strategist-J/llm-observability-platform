"""
Critical boundary and invariant tests for composite_scorer.
Rule: unit-tests.md — 100% coverage target for critical business rules.
"""
from __future__ import annotations
import pytest
from handlers.span_quality.composite_scorer import compute_composite, _WEIGHTS
from handlers.span_quality.types import ScoreMap


class TestCompositeScorerBoundaries:
    def test_all_perfect_scores_gives_max_composite(self):
        scores = ScoreMap(coherence=1.0, toxicity=0.0, faithfulness=1.0, perplexity=0.0)
        result = compute_composite(scores)
        assert result is not None
        assert result == pytest.approx(1.0, abs=0.001)

    def test_all_worst_scores_gives_zero_composite(self):
        """Worst: coherence=0, toxicity=1.0 (inverted=0), faithfulness=0, perplexity=inf"""
        scores = ScoreMap(coherence=0.0, toxicity=1.0, faithfulness=0.0, perplexity=9999.0)
        result = compute_composite(scores)
        assert result is not None
        assert result == pytest.approx(0.0, abs=0.01)

    def test_only_perplexity_present_returns_bounded_value(self):
        """perplexity=0 → 1/(1+0) = 1.0, should give composite close to 1."""
        scores = ScoreMap(perplexity=0.0)
        result = compute_composite(scores)
        assert result is not None
        assert result == pytest.approx(1.0, abs=0.001)

    def test_perplexity_only_very_high_returns_near_zero(self):
        """perplexity=999 → 1/(1+999) ≈ 0.001"""
        scores = ScoreMap(perplexity=999.0)
        result = compute_composite(scores)
        assert result is not None
        assert result < 0.01

    def test_toxicity_at_exactly_threshold_boundary(self):
        """toxicity=0.75 exactly: inverted = 0.25, weight=0.20"""
        scores = ScoreMap(toxicity=0.75)
        result = compute_composite(scores)
        assert result is not None
        assert result == pytest.approx(0.25, abs=0.001)

    def test_composite_never_exceeds_1(self):
        scores = ScoreMap(coherence=2.0, toxicity=-0.5, faithfulness=2.0)
        result = compute_composite(scores)
        assert result is not None
        assert result <= 1.0

    def test_composite_never_below_0(self):
        scores = ScoreMap(coherence=-1.0, toxicity=2.0, faithfulness=-1.0)
        result = compute_composite(scores)
        assert result is not None
        assert result >= 0.0

    def test_two_scores_use_correct_weight_renormalization(self):
        """Only coherence (w=0.35) and toxicity (w=0.20) present.
        composite = (0.35 * coh + 0.20 * (1-tox)) / (0.35 + 0.20)
        """
        coh, tox = 0.8, 0.2
        w_coh, w_tox = _WEIGHTS["coherence"], _WEIGHTS["toxicity"]
        expected = (w_coh * coh + w_tox * (1.0 - tox)) / (w_coh + w_tox)
        scores = ScoreMap(coherence=coh, toxicity=tox)
        result = compute_composite(scores)
        assert result == pytest.approx(expected, abs=1e-9)


class TestCompositeInvariantLogging:
    def test_invariant_violation_does_not_raise(self, caplog):
        """Invariant violations must LOG not RAISE — row must always be written."""
        import logging
        with caplog.at_level(logging.WARNING):
            result = compute_composite(ScoreMap(coherence=1.5))  # violates INV-Q-02
        # Must not raise; composite still returned
        assert result is not None

    def test_no_scores_returns_none_not_zero(self):
        """None is the sentinel for 'could not compute' — do NOT return 0 falsely."""
        assert compute_composite(ScoreMap()) is None
