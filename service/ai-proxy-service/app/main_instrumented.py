"""Example: Modified main.py with OpenTelemetry Integration

This example shows how to modify the main FastAPI application
to integrate OpenTelemetry with proper startup/shutdown handling.
"""

import logging
import sys

from fastapi.staticfiles import StaticFiles
from strawberry.fastapi import GraphQLRouter

from .config import app_state
from .routes import GenerateRequest, generate_endpoint, health_endpoint, router
from .schema import schema
from .telemetry_middleware import (
    create_instrumented_app,
    initialize_telemetry_for_service,
    shutdown_telemetry_for_service,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Create instrumented FastAPI app instead of plain FastAPI
app = create_instrumented_app(
    title="AI Proxy Service with OpenTelemetry",
    description="AI Proxy Service with comprehensive observability",
    version="1.0.0",
)

# Mount static files
app.mount(
    "/static",
    StaticFiles(directory="service/ai-proxy-service/app/static"),
    name="static",
)


@app.on_event("startup")
async def startup():
    """FastAPI startup event: loads configuration, initializes LLM providers, and telemetry."""
    logger.info("Starting AI Proxy Service: loading configuration")

    # Load configuration
    app_state.load_config()

    # Initialize LLM providers
    logger.info("Configuration loaded successfully: initializing LLM providers")
    await app_state.initialize_providers()

    if app_state.llm_providers:
        logger.info(
            "LLM providers initialized: %s", list(app_state.llm_providers.keys())
        )
    else:
        logger.warning("No LLM providers initialized")

    # Initialize telemetry with graceful degradation
    logger.info("Initializing telemetry...")
    telemetry_success = await initialize_telemetry_for_service(
        service_name="ai-proxy-service", service_version="1.0.0"
    )

    if telemetry_success:
        logger.info("Telemetry initialized successfully")
    else:
        logger.warning(
            "Telemetry initialization completed with limited functionality. "
            "Application will continue without full observability."
        )


@app.on_event("shutdown")
async def shutdown():
    """FastAPI shutdown event: cleanup resources."""
    logger.info("Shutting down AI Proxy Service")

    # Shutdown telemetry
    await shutdown_telemetry_for_service()

    logger.info("AI Proxy Service shutdown completed")


graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
app.include_router(router)


@app.get("/health")
async def health():
    """REST endpoint: returns the health status of the AI Proxy service."""
    logger.debug("Health endpoint called")
    return health_endpoint()


@app.post("/generate")
async def generate(req: GenerateRequest):
    """REST endpoint: generates text using a specified LLM provider."""
    logger.debug("Generate endpoint called with prompt length=%d", len(req.prompt))
    return await generate_endpoint(req)


@app.get("/telemetry/status")
async def telemetry_status():
    """
    Get telemetry status (for debugging)
    """
    from ...telemetry import get_telemetry_manager

    manager = get_telemetry_manager()
    if manager:
        return {
            "telemetry_enabled": True,
            "service_name": manager.service_name,
            "service_version": manager.service_version,
            "environment": manager.environment,
            "tracing_enabled": manager.enable_tracing,
            "metrics_enabled": manager.enable_metrics,
            "logging_enabled": manager.enable_logging,
            "otlp_endpoint": manager.otlp_endpoint,
        }
    return {
        "telemetry_enabled": False,
        "error": "Telemetry manager not initialized",
    }


if __name__ == "__main__":
    try:
        import uvicorn
    except ImportError:
        uvicorn = None
        logger.error("uvicorn not found. Please install it first.")

    if uvicorn:
        logger.info("Starting Uvicorn server on 0.0.0.0:8001")
        uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
    else:
        raise ImportError("uvicorn not found. Please install it first.")
