from __future__ import annotations

from fastapi import FastAPI

from api.rest.v1.router import router as v1_router
from shared.di.providers import build_gpt2_scorer, build_logprobs_scorer


def create_app() -> FastAPI:
    app = FastAPI(
        title="Perplexity Scorer",
        description="Layer 3 perplexity scoring — provider logprobs (primary) + GPT-2 ONNX fallback",
        version="0.1.0",
    )

    app.state.logprobs_scorer = build_logprobs_scorer()
    app.state.gpt2_scorer = build_gpt2_scorer()

    app.include_router(v1_router)
    return app


app = create_app()
