from __future__ import annotations

from fastapi import FastAPI

from api.rest.v1.router import router as v1_router
from infra.adapters.nli_scorer_adapter import NliScorerAdapter

def create_app() -> FastAPI:
    app = FastAPI(
        title="NLI Worker",
        description="Layer 3 stateless NLI worker — cross-encoder/nli-deberta-v3-base FastAPI inference server",
        version="0.1.0",
    )

    app.state.nli_scorer = NliScorerAdapter()
    app.include_router(v1_router)
    return app

app = create_app()
