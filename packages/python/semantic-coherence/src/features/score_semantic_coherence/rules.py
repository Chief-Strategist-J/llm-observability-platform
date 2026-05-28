from __future__ import annotations

from features.score_semantic_coherence.types import PromptType


THRESHOLDS: dict[str, float] = {
    "chat": 0.30,
    "code": 0.15,
    "rag": 0.25,
    "classification": 0.40,
}


def classify_coherence(score: float, prompt_type: PromptType) -> str:
    threshold = THRESHOLDS[prompt_type]
    if score < threshold:
        return "LOW_COHERENCE"
    return "OK"
