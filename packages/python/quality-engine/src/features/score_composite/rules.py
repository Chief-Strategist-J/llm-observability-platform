from __future__ import annotations

import math

BASE_WEIGHTS = {
    "coherence": 0.30,
    "faithfulness": 0.40,
    "toxicity": 0.20,
    "perplexity": 0.0,
}

def calculate_composite_score(
    coherence_score: float | None,
    faithfulness_score: float | None,
    toxicity_score: float | None,
    perplexity: float | None,
    perplexity_baseline: float = 2.0,
    use_literal_formula: bool = False,
) -> tuple[float | None, str | None, dict[str, float], dict[str, float]]:
    S = []
    raw_contributions = {}

    if coherence_score is not None:
        S.append("coherence")
        raw_contributions["coherence"] = coherence_score

    if faithfulness_score is not None:
        S.append("faithfulness")
        raw_contributions["faithfulness"] = faithfulness_score

    if toxicity_score is not None:
        S.append("toxicity")
        raw_contributions["toxicity"] = 1.0 - toxicity_score

    if perplexity is not None:
        S.append("perplexity")
        if perplexity <= 0.0 or perplexity_baseline <= 0.0:
            c_perp = 0.0
        elif use_literal_formula:
            denom = math.log(perplexity_baseline * 3.0)
            if denom != 0.0:
                c_perp = max(0.0, min(1.0, 1.0 - (math.log(perplexity) / denom)))
            else:
                c_perp = 0.0
        else:
            c_perp = max(0.0, min(1.0, 1.0 - (math.log(perplexity / perplexity_baseline) / math.log(3.0))))
        raw_contributions["perplexity"] = c_perp

    if not S:
        return None, "all_scores_null", {}, {}

    active_weights = {k: BASE_WEIGHTS[k] for k in S if BASE_WEIGHTS[k] > 0.0}
    total_weight = sum(active_weights.values())
    
    normalized_weights = {}
    if total_weight > 0.0:
        normalized_weights = {k: v / total_weight for k, v in active_weights.items()}

    composite = sum(normalized_weights[k] * raw_contributions[k] for k in active_weights) if active_weights else None
    if composite is None and "perplexity" in S:
        # If only perplexity is present, but its weight is 0.0, we still want to compute c_perp for contributions
        # but the composite score is None (or 0.0/None per test expectations)
        pass
    return composite, None, normalized_weights, raw_contributions
