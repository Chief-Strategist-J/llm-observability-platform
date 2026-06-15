from __future__ import annotations

from typing import Protocol


class ScorerClientPort(Protocol):
    def get_coherence_score(
        self,
        trace_id: str,
        span_id: str,
        prompt_type: str | None,
        pii_detected: bool | None,
        prompt_embedding: list[float] | None,
        response_embedding: list[float] | None,
    ) -> float | None:
        ...

    def get_faithfulness_score(
        self,
        trace_id: str,
        span_id: str,
        response_text: str | None,
        completion_tokens: int | None,
        rag_context: str | None,
        finish_reason: str | None,
    ) -> float | None:
        ...

    def get_toxicity_score(
        self,
        trace_id: str,
        span_id: str,
        response_text: str | None,
    ) -> float | None:
        ...

    def get_perplexity_value(
        self,
        trace_id: str,
        span_id: str,
        response_text: str | None,
        completion_tokens: int | None,
        prompt_type: str | None,
        token_logprobs: list[float] | None,
        finish_reason: str | None,
    ) -> float | None:
        ...

    def get_perplexity_result(
        self,
        trace_id: str,
        span_id: str,
        response_text: str | None,
        completion_tokens: int | None,
        prompt_type: str | None,
        token_logprobs: list[float] | None,
        finish_reason: str | None,
    ) -> tuple[float | None, bool]:
        """
        Returns (perplexity: float | None, high_perplexity: bool).
        high_perplexity is True when the perplexity-worker flagged the response
        as exceeding the high-perplexity threshold (p50 × 3.0).
        Returns (None, False) on timeout or scorer unavailability.
        """
        ...
