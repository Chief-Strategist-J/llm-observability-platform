from __future__ import annotations

from infra.adapters.scorers.cosine_scorer import CosineScorerAdapter


class MiniLMScorerAdapter(CosineScorerAdapter):
    def __init__(self) -> None:
        super().__init__(
            name="minilm",
            model_id="sentence-transformers/all-MiniLM-L6-v2",
        )
