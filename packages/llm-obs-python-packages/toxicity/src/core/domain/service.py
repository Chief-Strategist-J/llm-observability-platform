from __future__ import annotations

from core.domain.rules import determine_flag, is_flagged
from core.domain.types import ToxicityInput, ToxicityResult, ToxicityScores
from shared.tracing.tracer import trace_span


def score_toxicity(
    input: ToxicityInput,
    scorer: object,
    trace_id: str | None = None,
    span_id: str | None = None,
    publisher: object | None = None,
) -> ToxicityResult:
    """
    Score toxicity for a given input text.

    - Handles long texts (>510 tokens) via dual-pass (max-of-two strategy).
    - Optionally flags and publishes to Kafka when `publisher` is provided and
      the primary toxicity score exceeds the threshold.
    - Wraps execution in an OTel span, linking to the upstream trace context
      when trace_id / span_id are supplied.
    - Returns a unified ToxicityResult whether or not a publisher is wired in.
    """
    with trace_span(
        "toxicity.score",
        trace_id=trace_id,
        span_id=span_id,
        attributes={"input.length": len(input.text)},
    ) as main_span:
        try:
            token_ids: list[int] = scorer.tokenize(input.text)  # type: ignore[attr-defined]
            strategy: str | None = None

            if len(token_ids) <= 510:
                scores = scorer.score_token_ids(token_ids)  # type: ignore[attr-defined]
            else:
                # Dual-pass: score first 510 + last 510 tokens, take element-wise max
                first_ids = token_ids[:510]
                last_ids = token_ids[-510:]
                scores_first = scorer.score_token_ids(first_ids)  # type: ignore[attr-defined]
                scores_last = scorer.score_token_ids(last_ids)  # type: ignore[attr-defined]
                scores = ToxicityScores(
                    toxicity=max(scores_first.toxicity, scores_last.toxicity),
                    severe_toxicity=max(scores_first.severe_toxicity, scores_last.severe_toxicity),
                    obscene=max(scores_first.obscene, scores_last.obscene),
                    threat=max(scores_first.threat, scores_last.threat),
                    insult=max(scores_first.insult, scores_last.insult),
                    identity_hate=max(scores_first.identity_hate, scores_last.identity_hate),
                )
                strategy = "max_of_two_passes"

            primary_score = scores.toxicity
            flagged = is_flagged(primary_score)
            flag = determine_flag(primary_score)

            if flagged and publisher is not None:
                publisher.publish_flagged(  # type: ignore[attr-defined]
                    trace_id=trace_id or "",
                    span_id=span_id or "",
                    score=primary_score,
                    scores=scores,
                )

            main_span.set_attribute("output.score", primary_score)
            main_span.set_attribute("output.flagged", flagged)
            if strategy:
                main_span.set_attribute("output.strategy", strategy)
            main_span.set_attribute("skipped", False)

            return ToxicityResult(
                scores=scores,
                long_response_strategy=strategy,
                score=primary_score,
                flagged=flagged,
                flag=flag,
                skipped=False,
                skip_reason=None,
            )

        except Exception as e:
            main_span.set_attribute("skipped", True)
            main_span.set_attribute("skip_reason", "pipeline_failure")
            main_span.record_exception(e)
            return ToxicityResult(
                scores=ToxicityScores(
                    toxicity=0.0,
                    severe_toxicity=0.0,
                    obscene=0.0,
                    threat=0.0,
                    insult=0.0,
                    identity_hate=0.0,
                ),
                long_response_strategy=None,
                score=None,
                flagged=False,
                flag=None,
                skipped=True,
                skip_reason="pipeline_failure",
            )
