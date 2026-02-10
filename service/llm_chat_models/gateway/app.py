from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from config.settings import API_HOST, API_PORT
from telemetry.logger import log_event
from logic.agents.registry import AgentRegistry
from logic.agents.chat_agent import ChatAgent
from logic.agents.voice_agent import VoiceAgent


def create_app() -> FastAPI:
    """
    Application factory.

    Creates and configures the FastAPI instance, registers all routes,
    boots the agent registry, and instruments OpenTelemetry.
    """
    app = FastAPI(
        title="AI Agents Service",
        version="2.0.0",
        description=(
            "Extensible AI agents platform with durable workflow execution. "
            "Supports chat agents, voice agents (coming soon), and custom agent types."
        ),
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    from gateway.routes.health import router as health_router
    from gateway.routes.models import router as models_router
    from gateway.routes.agents import router as agents_router
    from gateway.routes.workflows import router as workflows_router

    app.include_router(health_router)
    app.include_router(models_router)
    app.include_router(agents_router)
    app.include_router(workflows_router)

    # Boot agent registry
    _register_agents()

    # Lifecycle events
    @app.on_event("startup")
    async def startup_event():
        log_event("service_startup", host=API_HOST, port=API_PORT)

    @app.on_event("shutdown")
    async def shutdown_event():
        log_event("service_shutdown")

    # OpenTelemetry instrumentation
    try:
        FastAPIInstrumentor.instrument_app(app)
        log_event("instrumentation_enabled")
    except Exception as e:
        log_event("instrumentation_failed", error=str(e))

    return app


def _register_agents():
    """Register all built-in agent types."""
    registry = AgentRegistry.get_instance()
    registry.register("chat", ChatAgent)
    registry.register("voice", VoiceAgent)
    log_event("agents_registered", types=["chat", "voice"])
