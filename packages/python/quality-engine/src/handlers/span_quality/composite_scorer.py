from __future__ import annotations

import logging
from handlers.span_quality.types import ScoreMap

logger = logging.getLogger(__name__)

# Score weights used in renormalization composite formula (F-Q-06)
# perplexity added as 4th dimension in Phase 3 (Step 3.2).
_WEIGHTS: dict[str, float] = {
    "coherence":    0.25,
    "faithfulness": 0.35,
    "toxicity":     0.15,  # inverted: (1 - toxicity)
    "perplexity":   0.10,  # normalized contribution: max(0, 1 - perplexity/200)
}

# Cap used to normalize raw perplexity float to [0, 1] contribution.
# At perplexity=0 → contribution=1.0 (best); at perplexity≥200 → contribution=0.0 (worst).
_PERPLEXITY_NORMALIZATION_CAP: float = 200.0


def _normalize_perplexity_contribution(perplexity: float) -> float:
    """
    Inline normalization: contribution = clamp(1 - perplexity/200, 0, 1).
    Higher perplexity → lower (worse) contribution.
    Avoids cross-package import from perplexity package.
    """
    return max(0.0, min(1.0, 1.0 - (perplexity / _PERPLEXITY_NORMALIZATION_CAP)))


def compute_composite(scores: ScoreMap) -> tuple[float | None, dict[str, float]]:
    """
    F-Q-06: Renormalization composite computation.
    Only uses scores that are available (non-null).
    Returns (None, {}) if no scores are available.
    Validates INV-Q-01 through INV-Q-07.

    Phase 3 change: perplexity (if not None) included as 4th dimension.
    When perplexity=None the 3-weight behaviour (coherence/faithfulness/toxicity)
    is preserved via dynamic renormalization — existing callers are unaffected.
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
        # Normalize raw perplexity float to quality contribution in [0, 1]
        available["perplexity"] = _normalize_perplexity_contribution(scores.perplexity)

    if not available:
        _validate_invariants(scores, None)
        return None, {}

    total_weight = sum(_WEIGHTS[k] for k in available if k in _WEIGHTS)
    if total_weight == 0.0:
        _validate_invariants(scores, None)
        return None, {}

    normalized_weights = {k: _WEIGHTS[k] / total_weight for k in available if k in _WEIGHTS}
    weighted_sum = sum(normalized_weights[k] * v for k, v in available.items() if k in normalized_weights)
    composite = weighted_sum

    # Clamp to [0, 1]
    composite = max(0.0, min(1.0, composite))

    _validate_invariants(scores, composite)
    return composite, normalized_weights


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

    if scores.toxicity is None:
        logger.warning("invariant_violation_total{invariant_id=INV-Q-07} toxicity_is_null")
