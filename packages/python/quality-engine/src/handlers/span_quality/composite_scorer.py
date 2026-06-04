from __future__ import annotations
import logging
from handlers.span_quality.types import ScoreMap

logger = logging.getLogger(__name__)

# Score weights used in renormalization composite formula (F-Q-06)
_WEIGHTS: dict[str, float] = {
    "coherence":    0.35,
    "faithfulness": 0.30,
    "toxicity":     0.20,  # inverted: (1 - toxicity)
    "perplexity":   0.15,  # inverted: 1 / (1 + perplexity_score)
}


def compute_composite(scores: ScoreMap) -> float | None:
    """
    F-Q-06: Renormalization composite computation.
    Only uses scores that are available (non-null).
    Returns None if no scores are available.
    Validates INV-Q-01 through INV-Q-07.
    """
    available: dict[str, float] = {}

    if scores.coherence is not None:
        available["coherence"] = scores.coherence
    if scores.faithfulness is not None:
        available["faithfulness"] = scores.faithfulness
    if scores.toxicity is not None:
        # F-Q-05: toxicity is a safety signal — inverted contribution
        available["toxicity"] = 1.0 - scores.toxicity
    if scores.perplexity is not None:
        # Normalize perplexity: bounded contribution 1/(1+x)
        available["perplexity"] = 1.0 / (1.0 + scores.perplexity)

    if not available:
        return None

    total_weight = sum(_WEIGHTS[k] for k in available)
    if total_weight == 0.0:
        return None

    weighted_sum = sum(_WEIGHTS[k] * v for k, v in available.items())
    composite = weighted_sum / total_weight

    # Clamp to [0, 1]
    composite = max(0.0, min(1.0, composite))

    _validate_invariants(scores, composite)
    return composite


def _validate_invariants(scores: ScoreMap, composite: float | None) -> None:
    """Log violations of INV-Q-01 through INV-Q-07 — do not raise, always write row."""
    if composite is not None and not (0.0 <= composite <= 1.0):
        logger.warning("invariant_violation_total{invariant_id=INV-Q-01} composite=%s", composite)

    if scores.coherence is not None and not (0.0 <= scores.coherence <= 1.0):
        logger.warning("invariant_violation_total{invariant_id=INV-Q-02} coherence=%s", scores.coherence)

    if scores.toxicity is not None and not (0.0 <= scores.toxicity <= 1.0):
        logger.warning("invariant_violation_total{invariant_id=INV-Q-03} toxicity=%s", scores.toxicity)

    if scores.faithfulness is not None and not (0.0 <= scores.faithfulness <= 1.0):
        logger.warning("invariant_violation_total{invariant_id=INV-Q-04} faithfulness=%s", scores.faithfulness)

    if scores.perplexity is not None and scores.perplexity < 0.0:
        logger.warning("invariant_violation_total{invariant_id=INV-Q-05} perplexity=%s", scores.perplexity)

    if composite is not None:
        has_any = any([scores.coherence, scores.toxicity, scores.faithfulness, scores.perplexity])
        if not has_any:
            logger.warning("invariant_violation_total{invariant_id=INV-Q-06} no_scores_for_non_null_composite")
