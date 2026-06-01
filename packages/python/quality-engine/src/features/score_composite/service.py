from __future__ import annotations

from features.score_composite.rules import calculate_composite_score
from features.score_composite.types import CompositeScoreInput, CompositeScoreResult
from shared.ports.alert_publisher_port import AlertPublisherPort
from shared.tracing.tracer import trace_span

def score_composite(
    input: CompositeScoreInput,
    alert_publisher: AlertPublisherPort,
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
        composite, skipped_reason, active_weights, raw_contributions = calculate_composite_score(
            coherence_score=input.coherence_score,
            faithfulness_score=input.faithfulness_score,
            toxicity_score=input.toxicity_score,
            perplexity=input.perplexity,
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
