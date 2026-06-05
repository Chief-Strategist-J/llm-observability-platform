from __future__ import annotations

from core.domain.types import (
    NliInput,
    NliResult,
    SentenceProbability,
    SentenceResult,
)
from infra.adapters.nli_scorer_adapter import NliScorerAdapter
from shared.tracing.tracer import trace_span

def score_nli(
    input: NliInput,
    scorer: NliScorerAdapter,
    trace_id: str | None = None,
    span_id: str | None = None,
) -> NliResult:
    with trace_span(
        "score_nli",
        trace_id=trace_id,
        span_id=span_id,
        attributes={
            "input.sentences_count": len(input.sentences),
            "input.context_length": len(input.context),
            "input.temperature": input.temperature,
        },
    ) as main_span:
        if not input.sentences:
            main_span.set_attribute("output.faithfulness_score", 1.0)
            return NliResult(
                results=[],
                faithfulness_score=1.0,
                flagged_sentences=[],
            )

        # 1. Context Chunking
        with trace_span(
            "nli.check_and_chunk",
            trace_id=trace_id,
            span_id=span_id,
        ) as chunk_span:
            context_tokens = scorer.count_tokens(input.context)
            chunk_span.set_attribute("nli.context_tokens", context_tokens)
            
            if context_tokens > 400:
                chunks = scorer.split_context_by_tokens(input.context, max_tokens=400)
                is_chunked = True
            else:
                chunks = [input.context]
                is_chunked = False
            
            chunk_span.set_attribute("nli.is_chunked", is_chunked)
            chunk_span.set_attribute("nli.chunk_count", len(chunks))

        # 2. Pair Generation
        pairs: list[tuple[str, str]] = []
        for chunk in chunks:
            for s in input.sentences:
                pairs.append((chunk, s))

        # 3. Model Inference
        with trace_span(
            "model_inference",
            trace_id=trace_id,
            span_id=span_id,
            attributes={
                "nli.model_id": scorer.model_id,
                "nli.device": scorer.device_name,
                "nli.pair_count": len(pairs),
            },
        ):
            raw_probs = scorer.score_pairs(pairs, temperature=input.temperature)

        # 4. Aggregation
        num_sentences = len(input.sentences)
        best_probs: list[tuple[float, float, float]] = []
        for i in range(num_sentences):
            # Select the chunk index that yields the maximum entailment probability (index 0)
            best_p = (-1.0, -1.0, -1.0)
            for j in range(len(chunks)):
                probs = raw_probs[j * num_sentences + i]
                if probs[0] > best_p[0]:
                    best_p = probs
            best_probs.append(best_p)

        # 5. Results & Faithfulness compilation
        results: list[SentenceResult] = []
        flagged_sentences: list[str] = []
        entailed_count = 0
        label_names = ["entailment", "neutral", "contradiction"]

        for i, s in enumerate(input.sentences):
            probs = best_probs[i]
            max_idx = probs.index(max(probs))
            pred_label = label_names[max_idx]

            results.append(
                SentenceResult(
                    sentence=s,
                    label=pred_label,
                    probabilities=SentenceProbability(
                        entailment=probs[0],
                        neutral=probs[1],
                        contradiction=probs[2],
                    ),
                )
            )

            if pred_label == "contradiction":
                flagged_sentences.append(s)
            if pred_label == "entailment":
                entailed_count += 1

        faithfulness_score = entailed_count / num_sentences
        main_span.set_attribute("output.faithfulness_score", faithfulness_score)

        return NliResult(
            results=results,
            faithfulness_score=faithfulness_score,
            flagged_sentences=flagged_sentences,
        )
