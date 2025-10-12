"""GraphQL schema module for AI Proxy Service.

Defines the Query and Mutation types for the service using Strawberry GraphQL.
Provides health checks and text generation endpoints through GraphQL.
Uses the central `app_state` singleton for configuration and LLM provider access.

"""

import logging

from fastapi import HTTPException
import strawberry

from ..core.domain.models import LLMRequest
from ..core.usecases.generate_text import generate_text
from .config import app_state  # Central singleton AppState instance

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@strawberry.type
class LLMResponse:
    """GraphQL type representing the response from an LLM.

    Attributes:
        text (str): Generated text from the LLM.
        provider (str): Name of the LLM provider.
        model (str): Model used by the LLM provider.

    """

    text: str
    provider: str
    model: str


@strawberry.type
class HealthStatus:
    """GraphQL type representing the health status of the AI Proxy Service.

    Attributes:
        status (str): Overall service status, usually "ok".
        providers (List[str]): List of available LLM providers.
        default (str): Default provider name from configuration.

    """

    status: str
    providers: list[str]
    default: str


@strawberry.type
class Query:
    """
    GraphQL Query type providing read-only endpoints.
    """

    @strawberry.field
    async def health(self) -> HealthStatus:
        """Returns the health status of the service including available LLM providers.

        Returns:
            HealthStatus: Object containing service status, provider list, and default provider.

        """
        providers = list(app_state.llm_providers.keys())
        default_provider = app_state.config.get("llm", {}).get("default", "none")
        logger.debug(
            "GraphQL health query requested. Providers: %s, Default: %s",
            providers,
            default_provider,
        )
        return HealthStatus(
            status="ok",
            providers=providers,
            default=default_provider,
        )


@strawberry.type
class Mutation:
    """
    GraphQL Mutation type providing write operations like text generation.
    """

    @strawberry.mutation
    async def generate_text(
        self,
        prompt: str,
        provider: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMResponse:
        """Generates text using a specified or default LLM provider.

        Args:
            prompt (str): The input text prompt for the LLM.
            provider (Optional[str]): Provider name to use; defaults to configuration default.
            max_tokens (Optional[int]): Maximum number of tokens to generate.
            temperature (Optional[float]): Sampling temperature controlling randomness.

        Returns:
            LLMResponse: Object containing generated text, provider, and model.

        Raises:
            HTTPException:
                - 400 if the requested provider is unavailable.
                - 500 if generation fails.

        """
        provider_name = provider or app_state.config.get("llm", {}).get(
            "default", "openai"
        )
        logger.debug(
            "GraphQL generate_text requested. Prompt: %s, Provider requested: %s",
            prompt,
            provider,
        )

        if provider_name not in app_state.llm_providers:
            logger.error("Provider '%s' not available", provider_name)
            raise HTTPException(400, f"Provider '{provider_name}' not available")

        provider_instance = app_state.llm_providers[provider_name]
        provider_config = app_state.config.get("llm", {}).get(provider_name, {})

        request = LLMRequest(
            prompt=prompt,
            provider=provider_name,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        logger.debug("Constructed LLMRequest: %s", request)

        try:
            response = await generate_text(
                request,
                provider_instance,
                provider_config.get("max_tokens", 1000),
                provider_config.get("temperature", 0.7),
            )
            logger.debug(
                "Generated response: Text length=%d, Provider=%s, Model=%s",
                len(response.text),
                response.provider,
                response.model,
            )
            return LLMResponse(
                text=response.text,
                provider=response.provider,
                model=response.model,
            )
        except Exception as e:
            logger.exception(
                "Text generation failed for provider '%s' with prompt '%s'",
                provider_name,
                prompt,
            )
            raise HTTPException(500, str(e)) from e


schema = strawberry.Schema(query=Query, mutation=Mutation)
