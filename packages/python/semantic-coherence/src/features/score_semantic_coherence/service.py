from __future__ import annotations

from features.score_semantic_coherence.rules import classify_coherence
from features.score_semantic_coherence.types import (
    CoherenceInput,
    CoherenceResult,
    ScorerOutput,
)
from shared.ports.scorer_port import ScorerPort


def score_semantic_coherence(
    input: CoherenceInput,
    scorers: list[ScorerPort],
    primary_scorer_name: str,
) -> CoherenceResult:
    if input.pii_detected:
        return CoherenceResult(
            prompt_type=input.prompt_type,
            skipped=True,
            skip_reason="pii_detected",
            primary=None,
            all_scores=[],
        )

    if input.prompt_embedding is None:
        return CoherenceResult(
            prompt_type=input.prompt_type,
            skipped=True,
            skip_reason="prompt_embedding_null",
            primary=None,
            all_scores=[],
        )

    if input.response_embedding is None:
        return CoherenceResult(
            prompt_type=input.prompt_type,
            skipped=True,
            skip_reason="response_embedding_null",
            primary=None,
            all_scores=[],
        )

    all_scores: list[ScorerOutput] = []
    for scorer in scorers:
        raw = scorer.compute(input.prompt_embedding, input.response_embedding)
        score = max(0.0, min(1.0, raw))
        label = classify_coherence(score, input.prompt_type)
        all_scores.append(
            ScorerOutput(
                scorer_name=scorer.name,
                scorer_model=scorer.model_id,
                score=score,
                label=label,
                skipped=False,
                skip_reason=None,
            )
        )

    primary = next(
        (s for s in all_scores if s.scorer_name == primary_scorer_name),
        all_scores[0] if all_scores else None,
    )

    return CoherenceResult(
        prompt_type=input.prompt_type,
        skipped=False,
        skip_reason=None,
        primary=primary,
        all_scores=all_scores,
    )
