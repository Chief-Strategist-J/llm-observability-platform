from fastapi import FastAPI
import os

from .router import api_v1_router
from ....infra.tracing.middleware import instrument_app

def create_app() -> FastAPI:
    app = FastAPI(title="Instrumentation SDK API", version="1.0.0")
    app.include_router(api_v1_router, prefix="/v1")
    instrument_app(app)
    return app

# The global app instance is created here for ASGI servers.
# To avoid side effects during tests, we can check for an environment variable.
if os.getenv("SKIP_APP_INIT") != "true":
    app = create_app()

# Build cache test
