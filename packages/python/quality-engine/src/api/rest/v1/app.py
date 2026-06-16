from __future__ import annotations

from fastapi import FastAPI

from prometheus_client import make_asgi_app
from api.rest.v1.router import router as v1_router
from shared.di.providers import build_alert_publisher, build_scorer_client, build_quality_score_repo

def create_app() -> FastAPI:
    app = FastAPI(
        title="Quality Engine",
        description="Layer 3 quality aggregation service",
        version="0.1.0",
    )

    app.mount("/metrics", make_asgi_app())
    app.state.alert_publisher = build_alert_publisher()
    app.state.scorer_client = build_scorer_client()
    app.state.repo = build_quality_score_repo()
    app.include_router(v1_router)
    return app


app = create_app()
