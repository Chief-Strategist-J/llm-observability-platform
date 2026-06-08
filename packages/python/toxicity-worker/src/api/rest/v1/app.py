from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI

from api.rest.v1.router import router as v1_router
from infra.adapters.detoxify_onnx_adapter import DetoxifyOnnxAdapter

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Eagerly load model and warmup tokenizer/model on startup
    scorer = app.state.toxicity_scorer
    if hasattr(scorer, "warmup"):
        scorer.warmup()
    yield

def create_app() -> FastAPI:
    app = FastAPI(
        title="Toxicity Worker",
        description="Layer 3 stateless toxicity worker — unitary/toxic-bert ONNX Runtime on CPU",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.state.toxicity_scorer = DetoxifyOnnxAdapter()
    app.include_router(v1_router)
    return app


app = create_app()
