from __future__ import annotations

import pytest

from shared.ports.scorer_port import ScorerPort
from infra.adapters.scorers.minilm_scorer import MiniLMScorerAdapter
from infra.adapters.scorers.scorer_registry import ScorerRegistry


def _satisfies_scorer_port(scorer: object) -> bool:
    return (
        hasattr(scorer, "name")
        and hasattr(scorer, "model_id")
        and callable(getattr(scorer, "compute", None))
    )


def test_minilm_satisfies_scorer_port_protocol() -> None:
    scorer = MiniLMScorerAdapter()
    assert _satisfies_scorer_port(scorer)


def test_minilm_name_is_stable() -> None:
    assert MiniLMScorerAdapter().name == "minilm"


def test_minilm_model_id_is_stable() -> None:
    assert MiniLMScorerAdapter().model_id == "sentence-transformers/all-MiniLM-L6-v2"


def test_new_scorer_can_be_added_without_changing_domain() -> None:
    class MPNetScorer:
        @property
        def name(self) -> str:
            return "mpnet"

        @property
        def model_id(self) -> str:
            return "sentence-transformers/all-mpnet-base-v2"

        def compute(self, prompt: list[float], response: list[float]) -> float:
            return 0.75

    scorer = MPNetScorer()
    assert _satisfies_scorer_port(scorer)
    registry = ScorerRegistry()
    registry.register(scorer)  # type: ignore[arg-type]
    assert registry.get("mpnet") is scorer


def test_scorer_registered_by_name_is_same_object() -> None:
    scorer = MiniLMScorerAdapter()
    registry = ScorerRegistry()
    registry.register(scorer)
    assert registry.get("minilm") is scorer


def test_registry_hot_swap_replaces_scorer_in_place() -> None:
    class V1Scorer:
        name = "my-scorer"
        model_id = "org/v1"
        def compute(self, p: list[float], r: list[float]) -> float:
            return 0.5

    class V2Scorer:
        name = "my-scorer"
        model_id = "org/v2"
        def compute(self, p: list[float], r: list[float]) -> float:
            return 0.8

    registry = ScorerRegistry()
    registry.register(V1Scorer())  # type: ignore[arg-type]
    assert registry.get("my-scorer").compute([], []) == 0.5  # type: ignore[union-attr]

    registry.register(V2Scorer())  # type: ignore[arg-type]
    assert registry.get("my-scorer").compute([], []) == 0.8  # type: ignore[union-attr]
    assert len(registry.all()) == 1


def test_multiple_scorers_do_not_interfere() -> None:
    class A:
        name = "a"
        model_id = "m/a"
        def compute(self, p: list[float], r: list[float]) -> float:
            return 0.2

    class B:
        name = "b"
        model_id = "m/b"
        def compute(self, p: list[float], r: list[float]) -> float:
            return 0.9

    registry = ScorerRegistry()
    registry.register(A())  # type: ignore[arg-type]
    registry.register(B())  # type: ignore[arg-type]

    assert registry.get("a").compute([], []) == 0.2  # type: ignore[union-attr]
    assert registry.get("b").compute([], []) == 0.9  # type: ignore[union-attr]


def test_scorer_port_is_structural_not_nominal() -> None:
    class ThirdPartyScorer:
        @property
        def name(self) -> str:
            return "third-party"

        @property
        def model_id(self) -> str:
            return "vendor/model"

        def compute(self, prompt: list[float], response: list[float]) -> float:
            import numpy as np
            a = np.array(prompt)
            b = np.array(response)
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

    scorer = ThirdPartyScorer()
    registry = ScorerRegistry()
    registry.register(scorer)  # type: ignore[arg-type]
    assert registry.get("third-party") is not None
    result = registry.get("third-party").compute([1.0, 0.0], [1.0, 0.0])  # type: ignore[union-attr]
    assert 0.99 < result <= 1.0
