from __future__ import annotations

import math

import pytest

from infra.adapters.scorers.minilm_scorer import MiniLMScorerAdapter
from features.score_semantic_coherence.service import score_semantic_coherence
from features.score_semantic_coherence.types import CoherenceInput
from features.score_semantic_coherence.rules import THRESHOLDS


_SCORER = MiniLMScorerAdapter()


def _unit(i: int, dim: int = 3) -> list[float]:
    v = [0.0] * dim
    v[i] = 1.0
    return v


def _scaled(scale: float, dim: int = 3) -> list[float]:
    return [scale] * dim


def test_real_cosine_identical_384d() -> None:
    emb = [0.5] * 384
    result = _SCORER.compute(emb, emb)
    assert math.isclose(result, 1.0, abs_tol=1e-5)


def test_real_cosine_orthogonal_384d() -> None:
    a = _unit(0, 384)
    b = _unit(1, 384)
    result = _SCORER.compute(a, b)
    assert math.isclose(result, 0.0, abs_tol=1e-5)


def test_real_cosine_45_degrees() -> None:
    a = [1.0, 0.0]
    b = [1.0, 1.0]
    result = _SCORER.compute(a, b)
    expected = 1.0 / math.sqrt(2)
    assert math.isclose(result, expected, abs_tol=1e-5)


def test_real_cosine_is_scale_invariant() -> None:
    a = [1.0, 0.0, 0.0]
    b = [0.5, 0.5, 0.0]
    result_1x = _SCORER.compute(a, b)
    result_100x = _SCORER.compute([x * 100 for x in a], [x * 100 for x in b])
    assert math.isclose(result_1x, result_100x, abs_tol=1e-5)


def test_real_cosine_symmetry() -> None:
    a = [0.3, 0.7, 0.1]
    b = [0.9, 0.1, 0.5]
    assert math.isclose(_SCORER.compute(a, b), _SCORER.compute(b, a), abs_tol=1e-6)


def test_real_cosine_both_zero_vectors() -> None:
    zero = [0.0, 0.0, 0.0]
    assert _SCORER.compute(zero, zero) == 0.0


@pytest.mark.parametrize("prompt_type,threshold", list(THRESHOLDS.items()))
def test_real_minilm_threshold_boundary_above(prompt_type: str, threshold: float) -> None:
    above_score = threshold + 0.05

    class FixedScorer:
        name = "fixed"
        model_id = "fixed/v1"
        def compute(self, p: list[float], r: list[float]) -> float:
            return above_score

    inp = CoherenceInput(
        prompt_type=prompt_type,  # type: ignore[arg-type]
        pii_detected=False,
        prompt_embedding=[1.0],
        response_embedding=[1.0],
    )
    result = score_semantic_coherence(inp, scorers=[FixedScorer()], primary_scorer_name="fixed")
    assert result.primary is not None
    assert result.primary.label == "OK", f"{prompt_type}: {above_score} should be OK"


@pytest.mark.parametrize("prompt_type,threshold", list(THRESHOLDS.items()))
def test_real_minilm_threshold_boundary_below(prompt_type: str, threshold: float) -> None:
    below_score = threshold - 0.01

    class FixedScorer:
        name = "fixed"
        model_id = "fixed/v1"
        def compute(self, p: list[float], r: list[float]) -> float:
            return below_score

    inp = CoherenceInput(
        prompt_type=prompt_type,  # type: ignore[arg-type]
        pii_detected=False,
        prompt_embedding=[1.0],
        response_embedding=[1.0],
    )
    result = score_semantic_coherence(inp, scorers=[FixedScorer()], primary_scorer_name="fixed")
    assert result.primary is not None
    assert result.primary.label == "LOW_COHERENCE", f"{prompt_type}: {below_score} should be LOW_COHERENCE"


@pytest.mark.parametrize("prompt_type,threshold", list(THRESHOLDS.items()))
def test_real_minilm_threshold_exact_boundary_is_ok(prompt_type: str, threshold: float) -> None:
    class FixedScorer:
        name = "fixed"
        model_id = "fixed/v1"
        def compute(self, p: list[float], r: list[float]) -> float:
            return threshold

    inp = CoherenceInput(
        prompt_type=prompt_type,  # type: ignore[arg-type]
        pii_detected=False,
        prompt_embedding=[1.0],
        response_embedding=[1.0],
    )
    result = score_semantic_coherence(inp, scorers=[FixedScorer()], primary_scorer_name="fixed")
    assert result.primary is not None
    assert result.primary.label == "OK", f"{prompt_type}: exactly at threshold should be OK"


def test_cosine_range_with_real_384d_vectors() -> None:
    import random
    random.seed(42)
    a = [random.gauss(0, 1) for _ in range(384)]
    b = [random.gauss(0, 1) for _ in range(384)]
    score = _SCORER.compute(a, b)
    assert -1.0 <= score <= 1.0


def test_clamp_enforced_when_service_receives_overconstrained_scorer() -> None:
    class OverflowScorer:
        name = "overflow"
        model_id = "overflow/v1"
        def compute(self, p: list[float], r: list[float]) -> float:
            return 1.5

    inp = CoherenceInput(
        prompt_type="chat",
        pii_detected=False,
        prompt_embedding=[1.0],
        response_embedding=[1.0],
    )
    result = score_semantic_coherence(inp, scorers=[OverflowScorer()], primary_scorer_name="overflow")
    assert result.primary is not None
    assert result.primary.score == 1.0


def test_clamp_enforced_for_negative_scorer() -> None:
    class NegScorer:
        name = "neg"
        model_id = "neg/v1"
        def compute(self, p: list[float], r: list[float]) -> float:
            return -0.99

    inp = CoherenceInput(
        prompt_type="rag",
        pii_detected=False,
        prompt_embedding=[1.0],
        response_embedding=[1.0],
    )
    result = score_semantic_coherence(inp, scorers=[NegScorer()], primary_scorer_name="neg")
    assert result.primary is not None
    assert result.primary.score == 0.0
