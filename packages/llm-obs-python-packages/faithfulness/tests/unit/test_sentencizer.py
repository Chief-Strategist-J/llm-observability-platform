from __future__ import annotations

import pytest

from infra.adapters.sentencizer.spacy_sentencizer import SpacySentencizerAdapter


@pytest.fixture(scope="module")
def adapter() -> SpacySentencizerAdapter:
    return SpacySentencizerAdapter()


def test_split_basic_sentences(adapter):
    text = "The cat sat on the mat. The dog ran away quickly. It was a nice day."
    result = adapter.split(text, min_words=3)
    assert len(result) == 3


def test_split_filters_short_sentences(adapter):
    text = "Yes. The cat sat on the mat outside the house today."
    result = adapter.split(text, min_words=5)
    assert all(len(s.split()) >= 5 for s in result)
    assert "Yes." not in result


def test_split_empty_text_returns_empty(adapter):
    result = adapter.split("", min_words=5)
    assert result == []


def test_split_min_words_zero_returns_all_sentences(adapter):
    text = "Yes. No. Maybe."
    result = adapter.split(text, min_words=0)
    assert len(result) >= 2


def test_split_strips_whitespace(adapter):
    text = "  The cat sat on the mat.  The dog ran away.  "
    result = adapter.split(text, min_words=3)
    for sentence in result:
        assert sentence == sentence.strip()


def test_split_returns_list_of_strings(adapter):
    text = "The quick brown fox jumped over the lazy dog."
    result = adapter.split(text, min_words=3)
    assert isinstance(result, list)
    assert all(isinstance(s, str) for s in result)
