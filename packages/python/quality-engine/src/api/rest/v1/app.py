from __future__ import annotations

from fastapi import FastAPI

from api.rest.v1.router import router as v1_router
from shared.di.providers import build_alert_publisher

def create_app() -> FastAPI:
    app = FastAPI(
        title="Quality Engine",
        description="Layer 3 quality aggregation service",
        version="0.1.0",
    )

    app.state.alert_publisher = build_alert_publisher()
    app.include_router(v1_router)
    return app

app = create_app()
