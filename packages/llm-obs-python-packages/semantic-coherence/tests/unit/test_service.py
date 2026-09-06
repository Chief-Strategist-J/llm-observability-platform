from features.score_semantic_coherence.service import score_semantic_coherence
from features.score_semantic_coherence.types import CoherenceInput


class FakeScorerOK:
    name = "fake_ok"
    model_id = "fake/ok-v1"

    def compute(self, prompt: list[float], response: list[float]) -> float:
        return 0.9


class FakeScorerLow:
    name = "fake_low"
    model_id = "fake/low-v1"

    def compute(self, prompt: list[float], response: list[float]) -> float:
        return 0.0


class FakeScorerNegative:
    name = "fake_neg"
    model_id = "fake/neg-v1"

    def compute(self, prompt: list[float], response: list[float]) -> float:
        return -0.5


def _emb(v: float) -> list[float]:
    return [v, 0.0, 0.0]


def test_single_scorer_ok_chat() -> None:
    inp = CoherenceInput(
        prompt_type="chat",
        pii_detected=False,
        prompt_embedding=_emb(1.0),
        response_embedding=_emb(1.0),
    )
    result = score_semantic_coherence(inp, scorers=[FakeScorerOK()], primary_scorer_name="fake_ok")
    assert result.skipped is False
    assert result.primary is not None
    assert result.primary.score == 0.9
    assert result.primary.label == "OK"


def test_single_scorer_low_chat() -> None:
    inp = CoherenceInput(
        prompt_type="chat",
        pii_detected=False,
        prompt_embedding=_emb(1.0),
        response_embedding=_emb(1.0),
    )
    result = score_semantic_coherence(inp, scorers=[FakeScorerLow()], primary_scorer_name="fake_low")
    assert result.primary is not None
    assert result.primary.score == 0.0
    assert result.primary.label == "LOW_COHERENCE"


def test_negative_cosine_clamped_to_zero() -> None:
    inp = CoherenceInput(
        prompt_type="chat",
        pii_detected=False,
        prompt_embedding=_emb(1.0),
        response_embedding=_emb(1.0),
    )
    result = score_semantic_coherence(inp, scorers=[FakeScorerNegative()], primary_scorer_name="fake_neg")
    assert result.primary is not None
    assert result.primary.score == 0.0


def test_multi_scorer_all_scores_returned() -> None:
    inp = CoherenceInput(
        prompt_type="rag",
        pii_detected=False,
        prompt_embedding=_emb(1.0),
        response_embedding=_emb(1.0),
    )
    result = score_semantic_coherence(
        inp,
        scorers=[FakeScorerOK(), FakeScorerLow()],
        primary_scorer_name="fake_ok",
    )
    assert len(result.all_scores) == 2
    names = {s.scorer_name for s in result.all_scores}
    assert names == {"fake_ok", "fake_low"}


def test_primary_scorer_selection() -> None:
    inp = CoherenceInput(
        prompt_type="code",
        pii_detected=False,
        prompt_embedding=_emb(1.0),
        response_embedding=_emb(1.0),
    )
    result = score_semantic_coherence(
        inp,
        scorers=[FakeScorerOK(), FakeScorerLow()],
        primary_scorer_name="fake_low",
    )
    assert result.primary is not None
    assert result.primary.scorer_name == "fake_low"


def test_primary_falls_back_to_first_when_not_found() -> None:
    inp = CoherenceInput(
        prompt_type="classification",
        pii_detected=False,
        prompt_embedding=_emb(1.0),
        response_embedding=_emb(1.0),
    )
    result = score_semantic_coherence(
        inp,
        scorers=[FakeScorerOK()],
        primary_scorer_name="nonexistent",
    )
    assert result.primary is not None
    assert result.primary.scorer_name == "fake_ok"


def test_all_four_prompt_types_produce_label() -> None:
    for pt in ("chat", "code", "rag", "classification"):
        inp = CoherenceInput(
            prompt_type=pt,  # type: ignore[arg-type]
            pii_detected=False,
            prompt_embedding=_emb(1.0),
            response_embedding=_emb(1.0),
        )
        result = score_semantic_coherence(inp, scorers=[FakeScorerOK()], primary_scorer_name="fake_ok")
        assert result.primary is not None
        assert result.primary.label in ("OK", "LOW_COHERENCE")
