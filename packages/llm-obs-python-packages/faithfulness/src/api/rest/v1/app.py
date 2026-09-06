from __future__ import annotations

from fastapi import FastAPI

from api.rest.v1.router import router as v1_router
from shared.di.providers import build_nli_scorer, build_sentencizer


def create_app() -> FastAPI:
    app = FastAPI(
        title="Faithfulness Scorer",
        description="Layer 3 faithfulness scoring — DeBERTa-v3-base NLI entailment fraction over RAG context",
        version="0.1.0",
    )

    app.state.nli_scorer = build_nli_scorer()
    app.state.sentencizer = build_sentencizer()

    app.include_router(v1_router)
    return app


app = create_app()
