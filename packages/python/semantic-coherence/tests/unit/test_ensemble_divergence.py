from __future__ import annotations

from features.score_semantic_coherence.service import score_semantic_coherence
from features.score_semantic_coherence.types import CoherenceInput


class DivergentScorer:
    def __init__(self, name: str, score: float) -> None:
        self._name = name
        self._score = score

    @property
    def name(self) -> str:
        return self._name

    @property
    def model_id(self) -> str:
        return f"model/{self._name}"

    def compute(self, prompt: list[float], response: list[float]) -> float:
        return self._score


_EMB = [1.0, 0.0, 0.0]


def _inp(prompt_type: str) -> CoherenceInput:
    return CoherenceInput(
        prompt_type=prompt_type,  # type: ignore[arg-type]
        pii_detected=False,
        prompt_embedding=_EMB,
        response_embedding=_EMB,
    )


def test_ensemble_both_agree_ok() -> None:
    s1 = DivergentScorer("a", 0.95)
    s2 = DivergentScorer("b", 0.85)
    result = score_semantic_coherence(_inp("chat"), scorers=[s1, s2], primary_scorer_name="a")
    assert len(result.all_scores) == 2
    assert all(s.label == "OK" for s in result.all_scores)


def test_ensemble_both_agree_low() -> None:
    s1 = DivergentScorer("a", 0.10)
    s2 = DivergentScorer("b", 0.05)
    result = score_semantic_coherence(_inp("chat"), scorers=[s1, s2], primary_scorer_name="a")
    assert all(s.label == "LOW_COHERENCE" for s in result.all_scores)


def test_ensemble_diverges_primary_is_respected() -> None:
    s_primary = DivergentScorer("primary", 0.95)
    s_secondary = DivergentScorer("secondary", 0.10)
    result = score_semantic_coherence(
        _inp("chat"),
        scorers=[s_primary, s_secondary],
        primary_scorer_name="primary",
    )
    assert result.primary is not None
    assert result.primary.scorer_name == "primary"
    assert result.primary.label == "OK"

    secondary = next(s for s in result.all_scores if s.scorer_name == "secondary")
    assert secondary.label == "LOW_COHERENCE"


def test_ensemble_secondary_is_primary() -> None:
    s1 = DivergentScorer("fast", 0.95)
    s2 = DivergentScorer("careful", 0.10)
    result = score_semantic_coherence(
        _inp("chat"),
        scorers=[s1, s2],
        primary_scorer_name="careful",
    )
    assert result.primary is not None
    assert result.primary.scorer_name == "careful"
    assert result.primary.label == "LOW_COHERENCE"


def test_ensemble_three_scorers_all_scores_independent() -> None:
    scorers = [
        DivergentScorer("high", 0.99),
        DivergentScorer("mid", 0.50),
        DivergentScorer("low", 0.05),
    ]
    result = score_semantic_coherence(_inp("chat"), scorers=scorers, primary_scorer_name="high")
    assert len(result.all_scores) == 3
    scores_by_name = {s.scorer_name: s.score for s in result.all_scores}
    assert scores_by_name["high"] == 0.99
    assert scores_by_name["mid"] == 0.50
    assert scores_by_name["low"] == 0.05


def test_ensemble_diverges_code_type() -> None:
    above = DivergentScorer("above_code", 0.20)
    below = DivergentScorer("below_code", 0.10)
    result = score_semantic_coherence(_inp("code"), scorers=[above, below], primary_scorer_name="above_code")
    above_result = next(s for s in result.all_scores if s.scorer_name == "above_code")
    below_result = next(s for s in result.all_scores if s.scorer_name == "below_code")
    assert above_result.label == "OK"
    assert below_result.label == "LOW_COHERENCE"


def test_ensemble_each_scorer_uses_same_input_independently() -> None:
    seen_prompts: list[list[float]] = []
    seen_responses: list[list[float]] = []

    class InspectingScorer:
        def __init__(self, name: str) -> None:
            self._name = name

        @property
        def name(self) -> str:
            return self._name

        @property
        def model_id(self) -> str:
            return "inspect/v1"

        def compute(self, prompt: list[float], response: list[float]) -> float:
            seen_prompts.append(list(prompt))
            seen_responses.append(list(response))
            return 0.5

    s1 = InspectingScorer("s1")
    s2 = InspectingScorer("s2")

    inp = CoherenceInput(
        prompt_type="rag",
        pii_detected=False,
        prompt_embedding=[0.1, 0.2, 0.3],
        response_embedding=[0.4, 0.5, 0.6],
    )
    score_semantic_coherence(inp, scorers=[s1, s2], primary_scorer_name="s1")

    assert len(seen_prompts) == 2
    assert seen_prompts[0] == seen_prompts[1]
    assert seen_responses[0] == seen_responses[1]
