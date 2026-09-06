from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from api.rest.v1.router import router as v1_router
from infra.adapters.detoxify_onnx_adapter import DetoxifyOnnxAdapter
from infra.adapters.kafka_publisher_adapter import KafkaToxicityPublisherAdapter


@asynccontextmanager
async def lifespan(app: FastAPI):
    scorer = app.state.toxicity_scorer
    if hasattr(scorer, "warmup"):
        scorer.warmup()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Toxicity Service",
        description=(
            "Unified toxicity service — stateless ONNX inference + optional Kafka publishing "
            "of flagged events. Accepts raw text or trace-linked requests."
        ),
        version="0.2.0",
        lifespan=lifespan,
    )

    # Prometheus metrics
    app.mount("/metrics", make_asgi_app())

    # ONNX scorer — model loaded lazily, warmed up in lifespan
    model_id = os.environ.get("TOXICITY_MODEL_ID", "unitary/toxic-bert")
    app.state.toxicity_scorer = DetoxifyOnnxAdapter(model_id=model_id)

    # Kafka publisher — disabled when KAFKA_BOOTSTRAP_SERVERS is unset
    bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
    app.state.toxicity_publisher = KafkaToxicityPublisherAdapter(
        bootstrap_servers=bootstrap_servers
    )

    app.include_router(v1_router)
    return app


app = create_app()
