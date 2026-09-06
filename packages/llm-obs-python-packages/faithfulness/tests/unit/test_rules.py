from __future__ import annotations

import pytest

from features.score_faithfulness.rules import (
    MIN_CONTEXT_CHARS,
    MIN_COMPLETION_TOKENS,
    BLOCKED_FINISH_REASONS,
    context_exceeds_limit,
    label_from_probs,
    should_skip,
    split_context_into_chunks,
    CONTEXT_CHUNK_TOKENS,
)
from features.score_faithfulness.types import FaithfulnessInput


def _input(**kwargs) -> FaithfulnessInput:
    defaults = dict(
        rag_context="This is a valid context with enough characters to pass the length check.",
        response_text="The model responded.",
        completion_tokens=20,
        finish_reason=None,
    )
    defaults.update(kwargs)
    return FaithfulnessInput(**defaults)


def test_should_skip_blocked_finish_reason():
    inp = _input(finish_reason="content_filter")
    skipped, reason = should_skip(inp)
    assert skipped is True
    assert reason == "finish_reason_blocked"


def test_should_skip_null_context():
    inp = _input(rag_context=None)
    skipped, reason = should_skip(inp)
    assert skipped is True
    assert reason == "rag_context_null"


def test_should_skip_context_too_short():
    inp = _input(rag_context="short")
    skipped, reason = should_skip(inp)
    assert skipped is True
    assert reason == "rag_context_too_short"


def test_should_skip_context_exactly_at_limit():
    context = "x" * MIN_CONTEXT_CHARS
    inp = _input(rag_context=context)
    skipped, reason = should_skip(inp)
    assert skipped is False
    assert reason is None


def test_should_skip_completion_tokens_too_few():
    inp = _input(completion_tokens=MIN_COMPLETION_TOKENS - 1)
    skipped, reason = should_skip(inp)
    assert skipped is True
    assert reason == "completion_tokens_too_few"


def test_should_skip_completion_tokens_exactly_at_limit():
    inp = _input(completion_tokens=MIN_COMPLETION_TOKENS)
    skipped, reason = should_skip(inp)
    assert skipped is False
    assert reason is None


def test_should_not_skip_valid_input():
    inp = _input()
    skipped, reason = should_skip(inp)
    assert skipped is False
    assert reason is None


@pytest.mark.parametrize("probs, expected_label", [
    ((0.9, 0.05, 0.05), "entailment"),
    ((0.05, 0.9, 0.05), "neutral"),
    ((0.05, 0.05, 0.9), "contradiction"),
    ((0.4, 0.4, 0.2), "entailment"),
])
def test_label_from_probs(probs, expected_label):
    assert label_from_probs(probs) == expected_label


def test_context_exceeds_limit_true():
    context = " ".join(["word"] * 513)
    assert context_exceeds_limit(context) is True


def test_context_exceeds_limit_false():
    context = " ".join(["word"] * 512)
    assert context_exceeds_limit(context) is False


def test_split_context_into_chunks_single():
    context = " ".join(["word"] * 100)
    chunks = split_context_into_chunks(context)
    assert len(chunks) == 1


def test_split_context_into_chunks_multiple():
    context = " ".join(["word"] * (CONTEXT_CHUNK_TOKENS * 2 + 10))
    chunks = split_context_into_chunks(context)
    assert len(chunks) == 3


def test_blocked_finish_reasons_contains_content_filter():
    assert "content_filter" in BLOCKED_FINISH_REASONS
