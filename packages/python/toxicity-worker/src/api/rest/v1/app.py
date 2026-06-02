from __future__ import annotations

from fastapi import FastAPI

from api.rest.v1.router import router as v1_router
from infra.adapters.detoxify_onnx_adapter import DetoxifyOnnxAdapter

def create_app() -> FastAPI:
    app = FastAPI(
        title="Toxicity Worker",
        description="Layer 3 stateless toxicity worker — unitary/toxic-bert ONNX Runtime on CPU",
        version="0.1.0",
    )

    app.state.toxicity_scorer = DetoxifyOnnxAdapter()
    app.include_router(v1_router)
    return app

app = create_app()
