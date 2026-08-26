from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .router import api_v1_router
from src.api.middleware.request_context import StandardRequestContextMiddleware
from src.infra.tracing.middleware import instrument_app
from src.features.spans.globals import set_reporter
from src.infra.messaging.producer.span_reporter import KafkaSpanReporter
from config.infra.env_config import service_config

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

    if service_config.kafka_bootstrap_servers:
        set_reporter(KafkaSpanReporter())

    instrument_app(app)
    return app

app = create_app()
