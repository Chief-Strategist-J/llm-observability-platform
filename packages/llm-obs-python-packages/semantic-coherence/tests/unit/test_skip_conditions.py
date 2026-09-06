from features.score_semantic_coherence.service import score_semantic_coherence
from features.score_semantic_coherence.types import CoherenceInput


class FakeScorer:
    name = "fake"
    model_id = "fake/v1"

    def compute(self, prompt: list[float], response: list[float]) -> float:
        return 0.9


_SCORER = FakeScorer()
_EMB = [1.0, 0.0, 0.0]


def test_skip_when_pii_detected() -> None:
    inp = CoherenceInput(
        prompt_type="chat",
        pii_detected=True,
        prompt_embedding=_EMB,
        response_embedding=_EMB,
    )
    result = score_semantic_coherence(inp, scorers=[_SCORER], primary_scorer_name="fake")
    assert result.skipped is True
    assert result.skip_reason == "pii_detected"
    assert result.primary is None
    assert result.all_scores == []


def test_skip_when_prompt_embedding_null() -> None:
    inp = CoherenceInput(
        prompt_type="chat",
        pii_detected=False,
        prompt_embedding=None,
        response_embedding=_EMB,
    )
    result = score_semantic_coherence(inp, scorers=[_SCORER], primary_scorer_name="fake")
    assert result.skipped is True
    assert result.skip_reason == "prompt_embedding_null"
    assert result.primary is None


def test_skip_when_response_embedding_null() -> None:
    inp = CoherenceInput(
        prompt_type="chat",
        pii_detected=False,
        prompt_embedding=_EMB,
        response_embedding=None,
    )
    result = score_semantic_coherence(inp, scorers=[_SCORER], primary_scorer_name="fake")
    assert result.skipped is True
    assert result.skip_reason == "response_embedding_null"
    assert result.primary is None


def test_pii_skip_takes_priority_over_null_embeddings() -> None:
    inp = CoherenceInput(
        prompt_type="chat",
        pii_detected=True,
        prompt_embedding=None,
        response_embedding=None,
    )
    result = score_semantic_coherence(inp, scorers=[_SCORER], primary_scorer_name="fake")
    assert result.skip_reason == "pii_detected"


def test_no_skip_when_all_inputs_valid() -> None:
    inp = CoherenceInput(
        prompt_type="rag",
        pii_detected=False,
        prompt_embedding=_EMB,
        response_embedding=_EMB,
    )
    result = score_semantic_coherence(inp, scorers=[_SCORER], primary_scorer_name="fake")
    assert result.skipped is False
    assert result.skip_reason is None
