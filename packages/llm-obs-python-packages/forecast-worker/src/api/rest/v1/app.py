from __future__ import annotations

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_client import make_asgi_app
from python_shared.discovery import ServiceRegistryManager, ServiceRegistryManagerOptions

from api.rest.v1.router import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    host = os.getenv("HOST") or os.getenv("SERVICE_HOST") or "localhost"
    port_env = os.getenv("PORT") or os.getenv("SERVICE_PORT")
    port = int(port_env) if port_env else 8006

    registry = ServiceRegistryManager(
        ServiceRegistryManagerOptions(
            name="forecast-worker",
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
        title="Temporal Forecast Worker API",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.mount("/metrics", make_asgi_app())
    app.include_router(router)
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
