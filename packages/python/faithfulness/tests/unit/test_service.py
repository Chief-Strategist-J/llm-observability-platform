from __future__ import annotations

import pytest

from features.score_faithfulness.service import score_faithfulness
from features.score_faithfulness.types import FaithfulnessInput


class FakeSentencizer:
    def __init__(self, sentences: list[str]) -> None:
        self._sentences = sentences

    def split(self, text: str, min_words: int) -> list[str]:
        return self._sentences


class FakeNliScorer:
    def __init__(
        self,
        probs: list[tuple[float, float, float]],
        model_id: str = "fake-model",
    ) -> None:
        self._probs = probs
        self._model_id = model_id
        self.calls: list[list[tuple[str, str]]] = []

    @property
    def model_id(self) -> str:
        return self._model_id

    def score_pairs(
        self, pairs: list[tuple[str, str]]
    ) -> list[tuple[float, float, float]]:
        self.calls.append(pairs)
        return self._probs[: len(pairs)]


def _valid_input(**kwargs) -> FaithfulnessInput:
    defaults = dict(
        rag_context="This is a valid context with sufficient character count for testing.",
        response_text="The model output text.",
        completion_tokens=20,
        finish_reason=None,
    )
    defaults.update(kwargs)
    return FaithfulnessInput(**defaults)


def test_skip_null_context():
    result = score_faithfulness(
        input=_valid_input(rag_context=None),
        sentencizer=FakeSentencizer([]),
        nli_scorer=FakeNliScorer([]),
    )
    assert result.skipped is True
    assert result.skip_reason == "rag_context_null"
    assert result.score is None


def test_skip_short_context():
    result = score_faithfulness(
        input=_valid_input(rag_context="short"),
        sentencizer=FakeSentencizer([]),
        nli_scorer=FakeNliScorer([]),
    )
    assert result.skipped is True
    assert result.skip_reason == "rag_context_too_short"


def test_skip_completion_tokens_too_few():
    result = score_faithfulness(
        input=_valid_input(completion_tokens=5),
        sentencizer=FakeSentencizer([]),
        nli_scorer=FakeNliScorer([]),
    )
    assert result.skipped is True
    assert result.skip_reason == "completion_tokens_too_few"


def test_skip_content_filter():
    result = score_faithfulness(
        input=_valid_input(finish_reason="content_filter"),
        sentencizer=FakeSentencizer([]),
        nli_scorer=FakeNliScorer([]),
    )
    assert result.skipped is True
    assert result.skip_reason == "finish_reason_blocked"


def test_skip_no_qualifying_sentences():
    result = score_faithfulness(
        input=_valid_input(),
        sentencizer=FakeSentencizer([]),
        nli_scorer=FakeNliScorer([]),
    )
    assert result.skipped is True
    assert result.skip_reason == "no_qualifying_sentences"
    assert result.total_qualifying == 0


def test_all_entailed_score_is_1():
    sentences = ["Sentence one.", "Sentence two."]
    probs = [(0.9, 0.05, 0.05), (0.85, 0.1, 0.05)]
    result = score_faithfulness(
        input=_valid_input(),
        sentencizer=FakeSentencizer(sentences),
        nli_scorer=FakeNliScorer(probs),
    )
    assert result.skipped is False
    assert result.score == pytest.approx(1.0)
    assert result.entailed_count == 2
    assert result.total_qualifying == 2
    assert all(r.label == "entailment" for r in result.sentence_results)


def test_partial_entailment_score():
    sentences = ["Sentence one.", "Sentence two.", "Sentence three."]
    probs = [
        (0.9, 0.05, 0.05),
        (0.05, 0.9, 0.05),
        (0.05, 0.05, 0.9),
    ]
    result = score_faithfulness(
        input=_valid_input(),
        sentencizer=FakeSentencizer(sentences),
        nli_scorer=FakeNliScorer(probs),
    )
    assert result.score == pytest.approx(1 / 3)
    assert result.entailed_count == 1
    assert result.total_qualifying == 3


def test_zero_entailment_score():
    sentences = ["Sentence one.", "Sentence two."]
    probs = [(0.05, 0.9, 0.05), (0.05, 0.05, 0.9)]
    result = score_faithfulness(
        input=_valid_input(),
        sentencizer=FakeSentencizer(sentences),
        nli_scorer=FakeNliScorer(probs),
    )
    assert result.score == pytest.approx(0.0)
    assert result.entailed_count == 0


def test_sentence_results_populated():
    sentences = ["The cat sat on the mat."]
    probs = [(0.8, 0.1, 0.1)]
    result = score_faithfulness(
        input=_valid_input(),
        sentencizer=FakeSentencizer(sentences),
        nli_scorer=FakeNliScorer(probs),
    )
    assert len(result.sentence_results) == 1
    assert result.sentence_results[0].sentence == sentences[0]
    assert result.sentence_results[0].label == "entailment"
    assert result.sentence_results[0].entailment_prob == pytest.approx(0.8)


def test_long_context_uses_chunked_scoring():
    long_context = " ".join(["word"] * 600)
    sentences = ["Sentence A.", "Sentence B."]
    probs_chunk1 = [(0.3, 0.5, 0.2), (0.6, 0.3, 0.1)]
    probs_chunk2 = [(0.8, 0.1, 0.1), (0.2, 0.6, 0.2)]

    call_count = [0]

    class ChunkedFakeNli:
        model_id = "fake"

        def score_pairs(self, pairs):
            idx = call_count[0]
            call_count[0] += 1
            if idx == 0:
                return probs_chunk1
            return probs_chunk2

    result = score_faithfulness(
        input=_valid_input(rag_context=long_context),
        sentencizer=FakeSentencizer(sentences),
        nli_scorer=ChunkedFakeNli(),
    )
    assert result.skipped is False
    assert result.sentence_results[0].entailment_prob == pytest.approx(0.8)
    assert result.sentence_results[1].entailment_prob == pytest.approx(0.6)
