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
from shared.tracing.tracer import trace_span


def score_faithfulness(
    input: FaithfulnessInput,
    sentencizer: SentencizerPort,
    nli_scorer: NliScorerPort,
    trace_id: str | None = None,
    span_id: str | None = None,
) -> FaithfulnessResult:
    with trace_span(
        "score_faithfulness",
        trace_id=trace_id,
        span_id=span_id,
        attributes={
            "input.completion_tokens": input.completion_tokens,
            "input.finish_reason": input.finish_reason,
            "input.has_context": input.rag_context is not None,
        },
    ) as main_span:
        skipped, skip_reason = should_skip(input)
        if skipped:
            main_span.set_attribute("skipped", True)
            main_span.set_attribute("skip_reason", skip_reason)
            return FaithfulnessResult(
                score=None,
                skipped=True,
                skip_reason=skip_reason,
                sentence_results=[],
                total_qualifying=None,
                entailed_count=None,
            )

        with trace_span("sentencizer.split", trace_id=trace_id, span_id=span_id) as sent_span:
            sentences = sentencizer.split(input.response_text, MIN_SENTENCE_WORDS)
            sent_span.set_attribute("output.sentence_count", len(sentences))

        if not sentences:
            main_span.set_attribute("skipped", True)
            main_span.set_attribute("skip_reason", "no_qualifying_sentences")
            return FaithfulnessResult(
                score=None,
                skipped=True,
                skip_reason="no_qualifying_sentences",
                sentence_results=[],
                total_qualifying=0,
                entailed_count=None,
            )

        context: str = input.rag_context  # type: ignore[assignment]

        is_chunked = context_exceeds_limit(context)
        main_span.set_attribute("is_chunked", is_chunked)

        with trace_span(
            "nli_scoring",
            trace_id=trace_id,
            span_id=span_id,
            attributes={
                "nli.model_id": getattr(nli_scorer, "model_id", "unknown"),
                "nli.is_chunked": is_chunked,
            },
        ) as nli_span:
            if is_chunked:
                chunks = split_context_into_chunks(context)
                nli_span.set_attribute("nli.chunk_count", len(chunks))
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

        main_span.set_attribute("output.score", score)
        main_span.set_attribute("output.entailed_count", entailed_count)
        main_span.set_attribute("output.total_qualifying", total)

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

