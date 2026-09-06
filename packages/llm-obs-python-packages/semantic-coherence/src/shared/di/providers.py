from __future__ import annotations

import os

from infra.adapters.embedding_worker.http_adapter import EmbeddingWorkerHttpAdapter
from infra.adapters.scorers.cosine_scorer import CosineScorerAdapter
from infra.adapters.scorers.scorer_registry import ScorerRegistry


_KNOWN_MODEL_IDS: dict[str, str] = {
    "minilm": "sentence-transformers/all-MiniLM-L6-v2",
    "mpnet": "sentence-transformers/all-mpnet-base-v2",
    "bge-small": "BAAI/bge-small-en-v1.5",
    "bge-base": "BAAI/bge-base-en-v1.5",
    "bge-large": "BAAI/bge-large-en-v1.5",
    "e5-small": "intfloat/e5-small-v2",
    "e5-base": "intfloat/e5-base-v2",
    "e5-large": "intfloat/e5-large-v2",
    "gte-small": "thenlper/gte-small",
    "gte-base": "thenlper/gte-base",
}


def _resolve_model_id(name: str) -> str:
    env_key = f"SCORER_{name.upper().replace('-', '_')}_MODEL_ID"
    return os.environ.get(env_key, _KNOWN_MODEL_IDS.get(name, f"custom/{name}"))


def build_scorer_registry() -> ScorerRegistry:
    registry = ScorerRegistry()

    raw = os.environ.get("SCORERS", "minilm")
    names = [n.strip() for n in raw.split(",") if n.strip()]

    for name in names:
        model_id = _resolve_model_id(name)
        registry.register(CosineScorerAdapter(name=name, model_id=model_id))

    return registry


def build_embedding_store() -> EmbeddingWorkerHttpAdapter:
    base_url = os.environ.get("EMBEDDING_WORKER_URL", "http://localhost:8080")
    return EmbeddingWorkerHttpAdapter(base_url=base_url)
