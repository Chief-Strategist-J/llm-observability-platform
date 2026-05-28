from __future__ import annotations

from shared.ports.scorer_port import ScorerPort


class ScorerRegistry:
    def __init__(self) -> None:
        self._scorers: dict[str, ScorerPort] = {}

    def register(self, scorer: ScorerPort) -> None:
        self._scorers[scorer.name] = scorer

    def get(self, name: str) -> ScorerPort | None:
        return self._scorers.get(name)

    def all(self) -> list[ScorerPort]:
        return list(self._scorers.values())

    def names(self) -> list[str]:
        return list(self._scorers.keys())

    def models(self) -> list[dict[str, str]]:
        return [
            {"name": s.name, "model_id": s.model_id}
            for s in self._scorers.values()
        ]
