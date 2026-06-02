from __future__ import annotations

from features.score_composite.rules import calculate_composite_score
from features.score_composite.types import CompositeScoreInput, CompositeScoreResult
from shared.ports.alert_publisher_port import AlertPublisherPort
from shared.ports.scorer_client_port import ScorerClientPort
from shared.tracing.tracer import trace_span

def score_composite(
    input: CompositeScoreInput,
    alert_publisher: AlertPublisherPort,
    scorer_client: ScorerClientPort | None = None,
) -> CompositeScoreResult:
    with trace_span(
        "score_composite",
        trace_id=input.trace_id,
        span_id=input.span_id,
        attributes={
            "input.coherence_score": input.coherence_score,
            "input.faithfulness_score": input.faithfulness_score,
            "input.toxicity_score": input.toxicity_score,
            "input.perplexity": input.perplexity,
            "input.perplexity_baseline": input.perplexity_baseline,
            "input.use_literal_formula": input.use_literal_formula,
        },
    ) as span:
        coh = input.coherence_score
        if coh is None and scorer_client is not None:
            coh = scorer_client.get_coherence_score(
                trace_id=input.trace_id,
                span_id=input.span_id,
                prompt_type=input.prompt_type,
                pii_detected=input.pii_detected,
                prompt_embedding=input.prompt_embedding,
                response_embedding=input.response_embedding,
            )

        faith = input.faithfulness_score
        if faith is None and scorer_client is not None:
            faith = scorer_client.get_faithfulness_score(
                trace_id=input.trace_id,
                span_id=input.span_id,
                response_text=input.response_text,
                completion_tokens=input.completion_tokens,
                rag_context=input.rag_context,
                finish_reason=input.finish_reason,
            )

        tox = input.toxicity_score
        if tox is None and scorer_client is not None:
            tox = scorer_client.get_toxicity_score(
                trace_id=input.trace_id,
                span_id=input.span_id,
                response_text=input.response_text,
            )

        perp = input.perplexity
        if perp is None and scorer_client is not None:
            perp = scorer_client.get_perplexity_value(
                trace_id=input.trace_id,
                span_id=input.span_id,
                response_text=input.response_text,
                completion_tokens=input.completion_tokens,
                prompt_type=input.prompt_type,
                token_logprobs=input.token_logprobs,
                finish_reason=input.finish_reason,
            )

        composite, skipped_reason, active_weights, raw_contributions = calculate_composite_score(
            coherence_score=coh,
            faithfulness_score=faith,
            toxicity_score=tox,
            perplexity=perp,
            perplexity_baseline=input.perplexity_baseline,
            use_literal_formula=input.use_literal_formula,
        )

        if skipped_reason == "all_scores_null":
            span.set_attribute("skipped", True)
            span.set_attribute("skip_reason", skipped_reason)
            alert_publisher.publish_alert(
                message="scoring pipeline is broken: all quality sub-metrics are null",
                metadata={"trace_id": input.trace_id, "span_id": input.span_id},
            )
        else:
            span.set_attribute("output.composite_score", composite)

        return CompositeScoreResult(
            trace_id=input.trace_id,
            span_id=input.span_id,
            composite_score=composite,
            quality_skipped_reason=skipped_reason,
            active_weights=active_weights,
            raw_contributions=raw_contributions,
        )
