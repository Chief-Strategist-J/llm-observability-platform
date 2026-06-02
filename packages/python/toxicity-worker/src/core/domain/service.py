from __future__ import annotations

from core.domain.ports.toxicity_scorer_port import ToxicityScorerPort
from core.domain.types import ToxicityInput, ToxicityResult, ToxicityScores
from shared.tracing.tracer import trace_span

def score_toxicity(
    input: ToxicityInput,
    scorer: ToxicityScorerPort,
    trace_id: str | None = None,
    span_id: str | None = None,
) -> ToxicityResult:
    with trace_span(
        "score_toxicity",
        trace_id=trace_id,
        span_id=span_id,
        attributes={
            "input.text_length": len(input.text),
        },
    ) as main_span:
        with trace_span("toxicity.tokenize", trace_id=trace_id, span_id=span_id) as tok_span:
            token_ids = scorer.tokenize(input.text)
            tok_span.set_attribute("output.token_count", len(token_ids))

        with trace_span("model_inference", trace_id=trace_id, span_id=span_id) as inf_span:
            if len(token_ids) <= 510:
                scores = scorer.score_token_ids(token_ids)
                strategy = None
            else:
                first_ids = token_ids[:510]
                last_ids = token_ids[-510:]
                scores_first = scorer.score_token_ids(first_ids)
                scores_last = scorer.score_token_ids(last_ids)
                scores = ToxicityScores(
                    toxicity=max(scores_first.toxicity, scores_last.toxicity),
                    severe_toxicity=max(scores_first.severe_toxicity, scores_last.severe_toxicity),
                    obscene=max(scores_first.obscene, scores_last.obscene),
                    threat=max(scores_first.threat, scores_last.threat),
                    insult=max(scores_first.insult, scores_last.insult),
                    identity_hate=max(scores_first.identity_hate, scores_last.identity_hate),
                )
                strategy = "max_of_two_passes"

        main_span.set_attribute("output.score", scores.toxicity)
        if strategy:
            main_span.set_attribute("output.strategy", strategy)

        return ToxicityResult(
            scores=scores,
            long_response_strategy=strategy,
        )
