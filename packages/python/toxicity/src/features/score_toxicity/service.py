from __future__ import annotations

from features.score_toxicity.rules import determine_flag, is_flagged
from features.score_toxicity.types import ToxicityInput, ToxicityResult, ToxicityScores
from shared.ports.toxicity_publisher_port import ToxicityPublisherPort
from shared.ports.toxicity_scorer_port import ToxicityScorerPort
from shared.tracing.tracer import trace_span

def score_toxicity(
    input: ToxicityInput,
    scorer: ToxicityScorerPort,
    publisher: ToxicityPublisherPort,
    trace_id: str | None = None,
    span_id: str | None = None,
) -> ToxicityResult:
    with trace_span(
        "score_toxicity",
        trace_id=trace_id,
        span_id=span_id,
        attributes={
            "input.text_length": len(input.response_text),
        },
    ) as main_span:
        try:
            with trace_span("toxicity.tokenize", trace_id=trace_id, span_id=span_id) as tok_span:
                token_ids = scorer.tokenize(input.response_text)
                tok_span.set_attribute("output.token_count", len(token_ids))

            with trace_span("model_inference", trace_id=trace_id, span_id=span_id) as inf_span:
                if len(token_ids) <= 510:
                    scores = scorer.score_token_ids(token_ids)
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

            primary_score = scores.toxicity
            flagged = is_flagged(primary_score)
            flag = determine_flag(primary_score)

            if flagged:
                publisher.publish_flagged(
                    trace_id=trace_id or "",
                    span_id=span_id or "",
                    score=primary_score,
                    scores=scores,
                )

            main_span.set_attribute("output.score", primary_score)
            main_span.set_attribute("output.flagged", flagged)
            main_span.set_attribute("skipped", False)

            return ToxicityResult(
                score=primary_score,
                flagged=flagged,
                flag=flag,
                skipped=False,
                skip_reason=None,
                scores=scores,
            )

        except Exception as e:
            main_span.set_attribute("skipped", True)
            main_span.set_attribute("skip_reason", "pipeline_failure")
            main_span.record_exception(e)
            return ToxicityResult(
                score=None,
                flagged=False,
                flag=None,
                skipped=True,
                skip_reason="pipeline_failure",
                scores=None,
            )
