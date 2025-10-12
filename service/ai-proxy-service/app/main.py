"""AI Proxy Service API.

This module provides a FastAPI-based REST and GraphQL API for the AI Proxy service,
which acts as a gateway to multiple LLM providers and handles events.

"""

import logging
import sys

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

from .config import app_state
from .routes import GenerateRequest, generate_endpoint, health_endpoint
from .schema import schema

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Proxy")


@app.on_event("startup")
async def startup():
    """FastAPI startup event: loads configuration and initializes LLM providers."""
    logger.info("Starting AI Proxy Service: loading configuration")
    app_state.load_config()
    logger.info("Configuration loaded successfully: initializing LLM providers")
    await app_state.initialize_providers()
    if app_state.llm_providers:
        logger.info(
            "LLM providers initialized: %s", list(app_state.llm_providers.keys())
        )
    else:
        logger.warning("No LLM providers initialized")


graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


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


if __name__ == "__main__":
    try:
        import uvicorn
    except ImportError:
        uvicorn = None
        logger.error("uvicorn not found. Please install it first.")

    if uvicorn:
        logger.info("Starting Uvicorn server on 0.0.0.0:8001")
        uvicorn.run(app, host="0.0.0.0", port=8001)
    else:
        raise ImportError("uvicorn not found. Please install it first.")
