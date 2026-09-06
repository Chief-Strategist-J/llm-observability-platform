from __future__ import annotations

import math
import pytest

from features.score_composite.rules import calculate_composite_score

def test_all_scores_present_perfect():
    comp, skipped, weights, raw = calculate_composite_score(
        coherence_score=1.0,
        faithfulness_score=1.0,
        toxicity_score=0.0,
        perplexity=2.0,
        perplexity_baseline=2.0,
        use_literal_formula=False,
    )
    assert skipped is None
    assert comp == pytest.approx(1.0)
    assert weights["coherence"] == pytest.approx(0.30 / 0.90)
    assert weights["faithfulness"] == pytest.approx(0.40 / 0.90)
    assert weights["toxicity"] == pytest.approx(0.20 / 0.90)
    assert weights.get("perplexity", 0.0) == pytest.approx(0.0)
    assert raw["coherence"] == pytest.approx(1.0)
    assert raw["faithfulness"] == pytest.approx(1.0)
    assert raw["toxicity"] == pytest.approx(1.0)
    assert raw["perplexity"] == pytest.approx(1.0)

def test_normalization_with_missing_scores():
    comp, skipped, weights, raw = calculate_composite_score(
        coherence_score=0.5,
        faithfulness_score=0.8,
        toxicity_score=None,
        perplexity=None,
    )
    assert skipped is None
    expected_comp = ((0.30 / 0.70) * 0.5) + ((0.40 / 0.70) * 0.8)
    assert comp == pytest.approx(expected_comp)
    assert weights["coherence"] == pytest.approx(3.0 / 7.0)
    assert weights["faithfulness"] == pytest.approx(4.0 / 7.0)
    assert "toxicity" not in weights
    assert "perplexity" not in weights

def test_perplexity_log_ratio_boundaries():
    comp_base, _, _, raw_base = calculate_composite_score(
        coherence_score=None,
        faithfulness_score=None,
        toxicity_score=None,
        perplexity=2.0,
        perplexity_baseline=2.0,
        use_literal_formula=False,
    )
    assert raw_base["perplexity"] == pytest.approx(1.0)

    comp_limit, _, _, raw_limit = calculate_composite_score(
        coherence_score=None,
        faithfulness_score=None,
        toxicity_score=None,
        perplexity=6.0,
        perplexity_baseline=2.0,
        use_literal_formula=False,
    )
    assert raw_limit["perplexity"] == pytest.approx(0.0)

    comp_clipped, _, _, raw_clipped = calculate_composite_score(
        coherence_score=None,
        faithfulness_score=None,
        toxicity_score=None,
        perplexity=100.0,
        perplexity_baseline=2.0,
        use_literal_formula=False,
    )
    assert raw_clipped["perplexity"] == pytest.approx(0.0)

    comp_clipped_low, _, _, raw_clipped_low = calculate_composite_score(
        coherence_score=None,
        faithfulness_score=None,
        toxicity_score=None,
        perplexity=0.5,
        perplexity_baseline=2.0,
        use_literal_formula=False,
    )
    assert raw_clipped_low["perplexity"] == pytest.approx(1.0)

def test_perplexity_literal_formula():
    comp_base, _, _, raw_base = calculate_composite_score(
        coherence_score=None,
        faithfulness_score=None,
        toxicity_score=None,
        perplexity=2.0,
        perplexity_baseline=2.0,
        use_literal_formula=True,
    )
    expected_perp = 1.0 - (math.log(2.0) / math.log(6.0))
    assert raw_base["perplexity"] == pytest.approx(expected_perp)

    comp_limit, _, _, raw_limit = calculate_composite_score(
        coherence_score=None,
        faithfulness_score=None,
        toxicity_score=None,
        perplexity=6.0,
        perplexity_baseline=2.0,
        use_literal_formula=True,
    )
    assert raw_limit["perplexity"] == pytest.approx(0.0)

def test_all_scores_null_scenario():
    comp, skipped, weights, raw = calculate_composite_score(
        coherence_score=None,
        faithfulness_score=None,
        toxicity_score=None,
        perplexity=None,
    )
    assert comp is None
    assert skipped == "all_scores_null"
    assert weights == {}
    assert raw == {}

def test_zero_or_negative_inputs():
    comp, skipped, weights, raw = calculate_composite_score(
        coherence_score=None,
        faithfulness_score=None,
        toxicity_score=None,
        perplexity=-1.0,
        perplexity_baseline=2.0,
    )
    assert raw["perplexity"] == pytest.approx(0.0)
