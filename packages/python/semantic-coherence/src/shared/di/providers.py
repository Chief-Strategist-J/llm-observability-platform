from __future__ import annotations

import os

from infra.adapters.embedding_worker.http_adapter import EmbeddingWorkerHttpAdapter
from infra.adapters.scorers.minilm_scorer import MiniLMScorerAdapter
from infra.adapters.scorers.scorer_registry import ScorerRegistry


def build_scorer_registry() -> ScorerRegistry:
    registry = ScorerRegistry()
    registry.register(MiniLMScorerAdapter())
    return registry


def build_embedding_store() -> EmbeddingWorkerHttpAdapter:
    base_url = os.environ.get(
        "EMBEDDING_WORKER_URL", "http://localhost:8080"
    )
    return EmbeddingWorkerHttpAdapter(base_url=base_url)
