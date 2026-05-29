from __future__ import annotations

from features.score_toxicity.types import ToxicityScores

TOXICITY_THRESHOLD = 0.50
TOXIC_RESPONSE_FLAG = "TOXIC_RESPONSE"

def is_flagged(score: float) -> bool:
    return score > TOXICITY_THRESHOLD

def determine_flag(score: float) -> str | None:
    if is_flagged(score):
        return TOXIC_RESPONSE_FLAG
    return None
