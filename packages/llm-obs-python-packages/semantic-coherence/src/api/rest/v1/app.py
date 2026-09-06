from __future__ import annotations

import os

from fastapi import FastAPI

from api.rest.v1.router import router as v1_router
from shared.di.providers import build_embedding_store, build_scorer_registry


def create_app() -> FastAPI:
    app = FastAPI(
        title="Semantic Coherence Scorer",
        description="Layer 3 semantic coherence scoring — multi-model, swappable via ScorerPort registry",
        version="0.1.0",
    )

    registry = build_scorer_registry()
    embedding_store = build_embedding_store()
    primary = os.environ.get("PRIMARY_SCORER", "minilm")

    app.state.scorer_registry = registry
    app.state.embedding_store = embedding_store
    app.state.primary_scorer_name = primary

    app.include_router(v1_router)
    return app


app = create_app()
