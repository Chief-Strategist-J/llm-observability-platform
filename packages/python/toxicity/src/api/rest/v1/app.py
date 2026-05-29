from __future__ import annotations

from fastapi import FastAPI

from api.rest.v1.router import router as v1_router
from shared.di.providers import build_toxicity_publisher, build_toxicity_scorer

def create_app() -> FastAPI:
    app = FastAPI(
        title="Toxicity Scorer",
        description="Layer 3 toxicity scoring — unitary/toxic-bert ONNX Runtime on CPU",
        version="0.1.0",
    )

    app.state.toxicity_scorer = build_toxicity_scorer()
    app.state.toxicity_publisher = build_toxicity_publisher()

    app.include_router(v1_router)
    return app

app = create_app()
