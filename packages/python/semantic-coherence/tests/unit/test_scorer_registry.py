from infra.adapters.scorers.minilm_scorer import MiniLMScorerAdapter
from infra.adapters.scorers.scorer_registry import ScorerRegistry


class AnotherFakeScorer:
    name = "mpnet"
    model_id = "sentence-transformers/all-mpnet-base-v2"

    def compute(self, prompt: list[float], response: list[float]) -> float:
        return 0.5


def test_register_and_retrieve_scorer() -> None:
    registry = ScorerRegistry()
    scorer = MiniLMScorerAdapter()
    registry.register(scorer)
    assert registry.get("minilm") is scorer


def test_all_returns_all_registered_scorers() -> None:
    registry = ScorerRegistry()
    registry.register(MiniLMScorerAdapter())
    registry.register(AnotherFakeScorer())
    scorers = registry.all()
    assert len(scorers) == 2


def test_names_returns_all_registered_names() -> None:
    registry = ScorerRegistry()
    registry.register(MiniLMScorerAdapter())
    registry.register(AnotherFakeScorer())
    assert set(registry.names()) == {"minilm", "mpnet"}


def test_models_returns_name_and_model_id() -> None:
    registry = ScorerRegistry()
    registry.register(MiniLMScorerAdapter())
    models = registry.models()
    assert models[0]["name"] == "minilm"
    assert models[0]["model_id"] == "sentence-transformers/all-MiniLM-L6-v2"


def test_get_unknown_scorer_returns_none() -> None:
    registry = ScorerRegistry()
    assert registry.get("unknown") is None


def test_register_replaces_same_name() -> None:
    registry = ScorerRegistry()
    registry.register(MiniLMScorerAdapter())
    registry.register(MiniLMScorerAdapter())
    assert len(registry.all()) == 1
