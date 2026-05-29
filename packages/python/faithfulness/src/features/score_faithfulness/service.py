from __future__ import annotations

from features.score_faithfulness.rules import (
    MIN_SENTENCE_WORDS,
    context_exceeds_limit,
    label_from_probs,
    should_skip,
    split_context_into_chunks,
)
from features.score_faithfulness.types import (
    FaithfulnessInput,
    FaithfulnessResult,
    SentenceResult,
)
from shared.ports.nli_scorer_port import NliScorerPort
from shared.ports.sentencizer_port import SentencizerPort


def score_faithfulness(
    input: FaithfulnessInput,
    sentencizer: SentencizerPort,
    nli_scorer: NliScorerPort,
) -> FaithfulnessResult:
    skipped, skip_reason = should_skip(input)
    if skipped:
        return FaithfulnessResult(
            score=None,
            skipped=True,
            skip_reason=skip_reason,
            sentence_results=[],
            total_qualifying=None,
            entailed_count=None,
        )

    sentences = sentencizer.split(input.response_text, MIN_SENTENCE_WORDS)

    if not sentences:
        return FaithfulnessResult(
            score=None,
            skipped=True,
            skip_reason="no_qualifying_sentences",
            sentence_results=[],
            total_qualifying=0,
            entailed_count=None,
        )

    context: str = input.rag_context  # type: ignore[assignment]

    if context_exceeds_limit(context):
        chunks = split_context_into_chunks(context)
        sentence_results = _score_with_chunked_context(sentences, chunks, nli_scorer)
    else:
        pairs = [(context, s) for s in sentences]
        raw_probs = nli_scorer.score_pairs(pairs)
        sentence_results = [
            SentenceResult(
                sentence=sentences[i],
                label=label_from_probs(raw_probs[i]),
                entailment_prob=raw_probs[i][0],
            )
            for i in range(len(sentences))
        ]

    entailed_count = sum(1 for r in sentence_results if r.label == "entailment")
    total = len(sentence_results)
    score = entailed_count / total if total > 0 else 0.0

    return FaithfulnessResult(
        score=score,
        skipped=False,
        skip_reason=None,
        sentence_results=sentence_results,
        total_qualifying=total,
        entailed_count=entailed_count,
    )


def _score_with_chunked_context(
    sentences: list[str],
    chunks: list[str],
    nli_scorer: NliScorerPort,
) -> list[SentenceResult]:
    best_entailment: list[float] = [0.0] * len(sentences)
    best_probs: list[tuple[float, float, float]] = [(0.0, 0.0, 0.0)] * len(sentences)

    for chunk in chunks:
        pairs = [(chunk, s) for s in sentences]
        chunk_probs = nli_scorer.score_pairs(pairs)
        for i, probs in enumerate(chunk_probs):
            if probs[0] > best_entailment[i]:
                best_entailment[i] = probs[0]
                best_probs[i] = probs

    return [
        SentenceResult(
            sentence=sentences[i],
            label=label_from_probs(best_probs[i]),
            entailment_prob=best_entailment[i],
        )
        for i in range(len(sentences))
    ]
