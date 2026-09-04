from __future__ import annotations

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from python_shared.discovery import ServiceRegistryManager, ServiceRegistryManagerOptions

from api.rest.v1.router import router as v1_router
from infra.adapters.nli_scorer_adapter import NliScorerAdapter

@asynccontextmanager
async def lifespan(app: FastAPI):
    scorer = app.state.nli_scorer
    if hasattr(scorer, "_model"):
        _ = scorer._model
    if hasattr(scorer, "_tokenizer"):
        _ = scorer._tokenizer

    host = os.getenv("HOST") or os.getenv("SERVICE_HOST") or "localhost"
    port_env = os.getenv("PORT") or os.getenv("SERVICE_PORT")
    port = int(port_env) if port_env else 8008

    registry = ServiceRegistryManager(
        ServiceRegistryManagerOptions(
            name="nli-worker",
            host=host,
            port=port,
            health_path="/health",
        )
    )
    await registry.register()

    try:
        yield
    finally:
        await registry.deregister()

def create_app() -> FastAPI:
    app = FastAPI(
        title="NLI Worker",
        description="Layer 3 stateless NLI worker — cross-encoder/nli-deberta-v3-base FastAPI inference server",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.state.nli_scorer = NliScorerAdapter()
    app.include_router(v1_router)
    return app

app = create_app()
