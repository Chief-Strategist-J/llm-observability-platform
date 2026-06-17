from __future__ import annotations
import pytest
from features.score_faithfulness.service import score_faithfulness
from features.score_faithfulness.types import FaithfulnessInput
from features.score_faithfulness.rules import (
    MIN_CONTEXT_CHARS,
    MIN_COMPLETION_TOKENS,
    MIN_SENTENCE_WORDS,
)

class _StaticSentencizer:
    def __init__(self, sentences: list[str]) -> None:
        self._sentences = sentences

    def split(self, text: str, min_words: int) -> list[str]:
        return self._sentences

class _MockNliScorer:
    def __init__(self, prob_responses: list[list[tuple[float, float, float]]] | None = None) -> None:
        self.calls: list[list[tuple[str, str]]] = []
        self._responses = iter(prob_responses) if prob_responses else None

    def score_pairs(self, pairs):
        self.calls.append(list(pairs))
        if self._responses:
            return next(self._responses)
        return [(0.9, 0.05, 0.05)] * len(pairs)

# ==============================================================================
# TEST-Q-04: Unit: faithfulness sentence splitting
# 15-sentence response → 15 NLI calls (evaluations)
# ==============================================================================
def test_faithfulness_sentence_splitting_15_sentences():
    # 15 distinct sentences, each having >= 5 words (MIN_SENTENCE_WORDS)
    sentences = [f"This is sentence number {i} here." for i in range(1, 16)]
    response_text = " ".join(sentences)
    
    inp = FaithfulnessInput(
        rag_context="x" * MIN_CONTEXT_CHARS,
        response_text=response_text,
        completion_tokens=200,
        finish_reason=None,
    )
    
    # We will use the static sentencizer that returns our 15 sentences
    sentencizer = _StaticSentencizer(sentences)
    nli_scorer = _MockNliScorer()
    
    res = score_faithfulness(inp, sentencizer, nli_scorer)
    
    assert res.skipped is False
    assert res.total_qualifying == 15
    # Verify that the NLI scorer received exactly 15 pairs
    assert len(nli_scorer.calls) == 1
    assert len(nli_scorer.calls[0]) == 15
    for i, pair in enumerate(nli_scorer.calls[0]):
        assert pair[0] == "x" * MIN_CONTEXT_CHARS  # context
        assert pair[1] == sentences[i]             # sentence


# ==============================================================================
# TEST-Q-05: Unit: context chunking
# 800-token context → split into 2 chunks, max entailment taken
# ==============================================================================
def test_context_chunking_800_tokens():
    # Create an 800-word context
    context = " ".join(["contextword"] * 800)
    
    # 1 sentence to evaluate
    sentences = ["This is a test sentence."]
    sentencizer = _StaticSentencizer(sentences)
    
    # We configure NLI scorer to return:
    # - first call (chunk 1): neutral (0.1, 0.8, 0.1)
    # - second call (chunk 2): entailment (0.9, 0.05, 0.05)
    # The max entailment should be taken, which is 0.9 (entailment)
    prob_responses = [
        [(0.1, 0.8, 0.1)],  # chunk 1 probabilities
        [(0.9, 0.05, 0.05)], # chunk 2 probabilities
    ]
    
    nli_scorer = _MockNliScorer(prob_responses)
    
    inp = FaithfulnessInput(
        rag_context=context,
        response_text=sentences[0],
        completion_tokens=MIN_COMPLETION_TOKENS,
        finish_reason=None,
    )
    
    res = score_faithfulness(inp, sentencizer, nli_scorer)
    
    assert res.skipped is False
    # Verify we had 2 chunks
    assert len(nli_scorer.calls) == 2
    # First chunk has 400 words, second chunk has 400 words (total 800 words)
    assert len(nli_scorer.calls[0][0][0].split()) == 400
    assert len(nli_scorer.calls[1][0][0].split()) == 400
    
    # Verify the result has took the max entailment probability across the 2 chunks
    assert res.sentence_results[0].label == "entailment"
    assert res.sentence_results[0].entailment_prob == pytest.approx(0.9)
    assert res.score == 1.0
