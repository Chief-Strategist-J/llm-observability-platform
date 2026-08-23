import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .router import api_v1_router
from src.api.middleware.request_context import StandardRequestContextMiddleware
from src.infra.tracing.middleware import instrument_app
from src.features.spans.globals import set_reporter
from src.infra.adapters.kafka.reliable_adapter import ReliableKafkaSpanReporter

def create_app() -> FastAPI:
    app = FastAPI(title="Instrumentation SDK API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(StandardRequestContextMiddleware)
    app.include_router(api_v1_router, prefix="/v1")

    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    if bootstrap_servers:
        set_reporter(ReliableKafkaSpanReporter(bootstrap_servers=bootstrap_servers))

    instrument_app(app)
    return app

app = create_app()
