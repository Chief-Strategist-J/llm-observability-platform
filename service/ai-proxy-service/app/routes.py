"""Endpoints module for AI Proxy Service.

This module defines REST endpoints for health checks and text generation using LLMs.
It uses Pydantic models for request validation and accesses the central application
state singleton to manage LLM provider instances and configuration.

Central configuration and provider initialization holder for the AI Proxy service
is defined as a singleton `app_state = AppState()`. It loads configuration from
../../config/providers.yaml and initializes LLM providers. This singleton exposes
`config` and `llm_providers` used by routes and GraphQL schema.

"""

import logging

from fastapi import HTTPException
from pydantic import BaseModel

from ..core.domain.models import LLMRequest
from ..core.usecases.generate_text import generate_text
from .config import app_state  # Central singleton AppState instance

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class GenerateRequest(BaseModel):
    """Pydantic model representing the structure of a text generation request.

    Attributes:
        prompt (str): The input text prompt to send to the LLM.
        provider (Optional[str]): The name of the LLM provider to use. If not specified,
            the default provider from the configuration is used.
        max_tokens (Optional[int]): Maximum number of tokens to generate. If not specified,
            defaults are used per provider configuration.
        temperature (Optional[float]): Sampling temperature for text generation,
            controlling randomness. Higher values produce more random outputs,
            lower values are more deterministic.

    """

    prompt: str
    provider: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None


def health_endpoint():
    """REST endpoint function for retrieving the health status of the AI Proxy service.

    Returns:
        dict: A dictionary containing service status, available providers, and default provider.

    """
    providers = list(app_state.llm_providers.keys())
    default_provider = app_state.config.get("llm", {}).get("default", "none")

    logger.debug(
        "Health check requested. Providers: %s, Default: %s",
        providers,
        default_provider,
    )

    return {
        "status": "ok",
        "providers": providers,
        "default": default_provider,
    }


async def generate_endpoint(req: GenerateRequest):
    """REST endpoint function for generating text using a specified LLM provider.

    Args:
        req (GenerateRequest): A validated Pydantic request object containing:
            - prompt: the text prompt to generate from.
            - provider: optional LLM provider to use; defaults to configured default.
            - max_tokens: optional maximum token limit.
            - temperature: optional sampling temperature.

    Returns:
        dict: Generated text along with provider and model details.

    Raises:
        HTTPException:
            - 400 if the requested provider is not available.
            - 500 if text generation fails.

    """
    provider_name = req.provider or app_state.config.get("llm", {}).get(
        "default", "openai"
    )
    logger.debug(
        "Generate request received. Prompt: %s, Provider requested: %s",
        req.prompt,
        req.provider,
    )
    logger.debug("Resolved provider to use: %s", provider_name)

    if provider_name not in app_state.llm_providers:
        logger.error("Provider '%s' not available", provider_name)
        raise HTTPException(400, f"Provider '{provider_name}' not available")

    provider = app_state.llm_providers[provider_name]
    provider_config = app_state.config.get("llm", {}).get(provider_name, {})

    logger.debug("Provider configuration: %s", provider_config)

    request = LLMRequest(
        prompt=req.prompt,
        provider=provider_name,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
    )
    logger.debug("Constructed LLMRequest: %s", request)

    try:
        response = await generate_text(
            request,
            provider,
            provider_config.get("max_tokens", 1000),
            provider_config.get("temperature", 0.7),
        )
        logger.debug(
            "Generated response: Text length=%d, Provider=%s, Model=%s",
            len(response.text),
            response.provider,
            response.model,
        )

        return {
            "text": response.text,
            "provider": response.provider,
            "model": response.model,
        }
    except Exception as e:
        logger.exception(
            "Text generation failed for provider '%s' with prompt '%s'",
            provider_name,
            req.prompt,
        )
        raise HTTPException(500, str(e)) from e
