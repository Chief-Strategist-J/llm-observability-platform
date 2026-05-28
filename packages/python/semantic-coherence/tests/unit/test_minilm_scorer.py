import math

from infra.adapters.scorers.minilm_scorer import MiniLMScorerAdapter


_SCORER = MiniLMScorerAdapter()


def test_name() -> None:
    assert _SCORER.name == "minilm"


def test_model_id() -> None:
    assert _SCORER.model_id == "sentence-transformers/all-MiniLM-L6-v2"


def test_identical_vectors_score_one() -> None:
    emb = [1.0, 0.0, 0.0]
    result = _SCORER.compute(emb, emb)
    assert math.isclose(result, 1.0, abs_tol=1e-6)


def test_orthogonal_vectors_score_zero() -> None:
    a = [1.0, 0.0, 0.0]
    b = [0.0, 1.0, 0.0]
    result = _SCORER.compute(a, b)
    assert math.isclose(result, 0.0, abs_tol=1e-6)


def test_opposite_vectors_score_negative_one() -> None:
    a = [1.0, 0.0, 0.0]
    b = [-1.0, 0.0, 0.0]
    result = _SCORER.compute(a, b)
    assert math.isclose(result, -1.0, abs_tol=1e-6)


def test_zero_norm_vector_returns_zero() -> None:
    zero = [0.0, 0.0, 0.0]
    emb = [1.0, 0.0, 0.0]
    assert _SCORER.compute(zero, emb) == 0.0
    assert _SCORER.compute(emb, zero) == 0.0


def test_high_dim_similar_vectors() -> None:
    a = [0.5] * 384
    b = [0.5] * 384
    result = _SCORER.compute(a, b)
    assert math.isclose(result, 1.0, abs_tol=1e-5)
