from __future__ import annotations

from features.score_perplexity.rules import (
    WEIGHT_ACTIVE,
    WEIGHT_SKIPPED,
    compute_perplexity_from_logprobs,
    is_high_perplexity,
    normalize_contribution,
    should_skip,
)
from features.score_perplexity.types import PerplexityInput, PerplexityResult
from shared.ports.gpt2_scorer_port import Gpt2ScorerPort
from shared.ports.logprobs_scorer_port import LogprobsScorerPort
from shared.tracing.tracer import trace_span


def score_perplexity(
    input: PerplexityInput,
    logprobs_scorer: LogprobsScorerPort,
    gpt2_scorer: Gpt2ScorerPort,
    trace_id: str | None = None,
    span_id: str | None = None,
) -> PerplexityResult:
    with trace_span(
        "score_perplexity",
        trace_id=trace_id,
        span_id=span_id,
        attributes={
            "input.completion_tokens": input.completion_tokens,
            "input.finish_reason": input.finish_reason,
            "input.prompt_type": input.prompt_type,
            "input.has_token_logprobs": input.token_logprobs is not None,
        },
    ) as main_span:
        skipped, skip_reason = should_skip(input)
        if skipped:
            main_span.set_attribute("skipped", True)
            main_span.set_attribute("skip_reason", skip_reason)
            return PerplexityResult(
                perplexity=None,
                score=None,
                weight=WEIGHT_SKIPPED,
                skipped=True,
                skip_reason=skip_reason,
                high_perplexity_flag=False,
                prompt_type=input.prompt_type,
                scorer_used=None,
            )

        perplexity, scorer_used = _resolve_perplexity(input, logprobs_scorer, gpt2_scorer, trace_id, span_id)

        if perplexity is None:
            main_span.set_attribute("skipped", True)
            main_span.set_attribute("skip_reason", "scorer_unavailable")
            return PerplexityResult(
                perplexity=None,
                score=None,
                weight=WEIGHT_SKIPPED,
                skipped=True,
                skip_reason="scorer_unavailable",
                high_perplexity_flag=False,
                prompt_type=input.prompt_type,
                scorer_used=None,
            )

        flag = is_high_perplexity(perplexity, input.prompt_type)
        contribution = normalize_contribution(perplexity, input.prompt_type)

        main_span.set_attribute("output.perplexity", perplexity)
        main_span.set_attribute("output.score", contribution)
        main_span.set_attribute("output.high_perplexity_flag", flag)
        main_span.set_attribute("output.scorer_used", scorer_used or "")

        return PerplexityResult(
            perplexity=perplexity,
            score=contribution,
            weight=WEIGHT_ACTIVE,
            skipped=False,
            skip_reason=None,
            high_perplexity_flag=flag,
            prompt_type=input.prompt_type,
            scorer_used=scorer_used,
        )


def _resolve_perplexity(
    input: PerplexityInput,
    logprobs_scorer: LogprobsScorerPort,
    gpt2_scorer: Gpt2ScorerPort,
    trace_id: str | None,
    span_id: str | None,
) -> tuple[float | None, str | None]:
    with trace_span("perplexity.provider_logprobs", trace_id=trace_id, span_id=span_id) as lp_span:
        result = logprobs_scorer.compute(input.token_logprobs, input.response_text)
        lp_span.set_attribute("provider_logprobs.available", result is not None)
        if result is not None:
            return result, "provider_logprobs"

    with trace_span("perplexity.gpt2_fallback", trace_id=trace_id, span_id=span_id) as gpt_span:
        gpt_span.set_attribute("gpt2.available", gpt2_scorer.is_available())
        if not gpt2_scorer.is_available():
            return None, None
        result = gpt2_scorer.compute(input.response_text)
        return result, "gpt2_onnx"
