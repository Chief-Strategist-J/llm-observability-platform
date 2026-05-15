from fastapi import FastAPI
import os

from .router import api_v1_router
from ....infra.tracing.middleware import instrument_app

def create_app() -> FastAPI:
    app = FastAPI(title="Instrumentation SDK API", version="1.0.0")
    app.include_router(api_v1_router, prefix="/v1")
    instrument_app(app)
    return app

# Always define the app instance for ASGI servers like uvicorn
app = create_app()

# Build cache test
