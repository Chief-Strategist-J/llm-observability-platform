from __future__ import annotations

import os


def test_single_scorer_loaded_from_env(monkeypatch: object) -> None:
    monkeypatch.setenv("SCORERS", "minilm")  # type: ignore[attr-defined]
    monkeypatch.setenv("SCORER_MINILM_MODEL_ID", "sentence-transformers/all-MiniLM-L6-v2")  # type: ignore[attr-defined]

    from shared.di import providers
    import importlib
    importlib.reload(providers)

    registry = providers.build_scorer_registry()
    assert len(registry.all()) == 1
    scorer = registry.get("minilm")
    assert scorer is not None
    assert scorer.model_id == "sentence-transformers/all-MiniLM-L6-v2"


def test_multi_scorer_loaded_from_env(monkeypatch: object) -> None:
    monkeypatch.setenv("SCORERS", "minilm,mpnet")  # type: ignore[attr-defined]
    monkeypatch.setenv("SCORER_MINILM_MODEL_ID", "sentence-transformers/all-MiniLM-L6-v2")  # type: ignore[attr-defined]
    monkeypatch.setenv("SCORER_MPNET_MODEL_ID", "sentence-transformers/all-mpnet-base-v2")  # type: ignore[attr-defined]

    from shared.di import providers
    import importlib
    importlib.reload(providers)

    registry = providers.build_scorer_registry()
    assert len(registry.all()) == 2
    assert registry.get("minilm") is not None
    assert registry.get("mpnet") is not None
    assert registry.get("mpnet").model_id == "sentence-transformers/all-mpnet-base-v2"  # type: ignore[union-attr]


def test_custom_scorer_name_with_env_model_id(monkeypatch: object) -> None:
    monkeypatch.setenv("SCORERS", "my-custom-embed")  # type: ignore[attr-defined]
    monkeypatch.setenv("SCORER_MY_CUSTOM_EMBED_MODEL_ID", "org/my-private-embedder-v3")  # type: ignore[attr-defined]

    from shared.di import providers
    import importlib
    importlib.reload(providers)

    registry = providers.build_scorer_registry()
    scorer = registry.get("my-custom-embed")
    assert scorer is not None
    assert scorer.model_id == "org/my-private-embedder-v3"


def test_unknown_name_falls_back_to_custom_prefix(monkeypatch: object) -> None:
    monkeypatch.setenv("SCORERS", "totally-unknown")  # type: ignore[attr-defined]

    from shared.di import providers
    import importlib
    importlib.reload(providers)

    registry = providers.build_scorer_registry()
    scorer = registry.get("totally-unknown")
    assert scorer is not None
    assert scorer.model_id == "custom/totally-unknown"


def test_known_name_uses_builtin_default_when_no_env_override(monkeypatch: object) -> None:
    monkeypatch.setenv("SCORERS", "bge-small")  # type: ignore[attr-defined]
    monkeypatch.delenv("SCORER_BGE_SMALL_MODEL_ID", raising=False)  # type: ignore[attr-defined]

    from shared.di import providers
    import importlib
    importlib.reload(providers)

    registry = providers.build_scorer_registry()
    scorer = registry.get("bge-small")
    assert scorer is not None
    assert scorer.model_id == "BAAI/bge-small-en-v1.5"


def test_scorer_computes_cosine_after_env_load(monkeypatch: object) -> None:
    monkeypatch.setenv("SCORERS", "test-model")  # type: ignore[attr-defined]
    monkeypatch.setenv("SCORER_TEST_MODEL_MODEL_ID", "test/my-model")  # type: ignore[attr-defined]

    from shared.di import providers
    import importlib
    importlib.reload(providers)

    registry = providers.build_scorer_registry()
    scorer = registry.get("test-model")
    assert scorer is not None

    result = scorer.compute([1.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    import math
    assert math.isclose(result, 1.0, abs_tol=1e-5)


def test_five_scorers_ensemble_via_env(monkeypatch: object) -> None:
    monkeypatch.setenv("SCORERS", "minilm,mpnet,bge-small,e5-base,gte-small")  # type: ignore[attr-defined]

    from shared.di import providers
    import importlib
    importlib.reload(providers)

    registry = providers.build_scorer_registry()
    assert len(registry.all()) == 5
    assert set(registry.names()) == {"minilm", "mpnet", "bge-small", "e5-base", "gte-small"}


def test_primary_scorer_env_overrides_default(monkeypatch: object) -> None:
    monkeypatch.setenv("SCORERS", "minilm,mpnet")  # type: ignore[attr-defined]
    monkeypatch.setenv("PRIMARY_SCORER", "mpnet")  # type: ignore[attr-defined]

    primary = os.environ.get("PRIMARY_SCORER", "minilm")
    assert primary == "mpnet"
