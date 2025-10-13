import logging
import os

from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ..core.domain.models import LLMRequest
from ..core.usecases.generate_text import generate_text
from .config import app_state

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

router = APIRouter()
templates = Jinja2Templates(directory="service/ai-proxy-service/app/templates")


class MultiProviderSetupRequest(BaseModel):
    """
    Pydantic model representing a multi-provider setup request.
    """

    openai_key: str | None = None
    anthropic_key: str | None = None
    grok_key: str | None = None
    cloudflare_token: str | None = None
    cloudflare_account: str | None = None


class SetupRequest(BaseModel):
    """
    Pydantic model representing a provider setup request.
    """

    provider: str
    api_key: str


class GenerateRequest(BaseModel):
    """
    Pydantic model representing a text generation request.
    """

    prompt: str
    provider: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None


def health_endpoint():
    """
    Return the health status of the AI Proxy service.
    """
    providers = list(app_state.llm_providers.keys())
    default_provider = app_state.config.get("llm", {}).get("default", "none")
    return {"status": "ok", "providers": providers, "default": default_provider}


async def generate_endpoint(req: GenerateRequest):
    """
    Generate text using a specified LLM provider.
    """
    provider_name = req.provider or app_state.config.get("llm", {}).get(
        "default", "openai"
    )
    if provider_name not in app_state.llm_providers:
        raise HTTPException(400, f"Provider '{provider_name}' not available")
    provider = app_state.llm_providers[provider_name]
    provider_config = app_state.config.get("llm", {}).get(provider_name, {})
    request = LLMRequest(
        prompt=req.prompt,
        provider=provider_name,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
    )
    try:
        response = await generate_text(
            request,
            provider,
            provider_config.get("max_tokens", 1000),
            provider_config.get("temperature", 0.7),
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


@router.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    """
    Serve the HTML setup page.
    """
    return templates.TemplateResponse("setup.html", {"request": request})


@router.post("/setup")
async def save_setup(req: SetupRequest = Body(...)):
    """
    Save provider API key to user configuration and reload providers.
    """
    provider = req.provider
    api_key = req.api_key
    try:
        app_state.save_user_config(provider, api_key)
        app_state.initialize_providers()
        return JSONResponse({"message": f"Provider '{provider}' saved successfully!"})
    except ValueError as e:
        logger.exception("Failed to save provider '%s'", provider)
        return JSONResponse(
            {"message": f"Failed to save provider: {e}"}, status_code=400
        )
    except FileNotFoundError as e:
        logger.exception("Failed to save provider '%s'", provider)
        return JSONResponse(
            {"message": f"Failed to save provider: {e}"}, status_code=400
        )
    except Exception as e:
        logger.exception("Failed to save provider '%s'", provider)
        return JSONResponse(
            {"message": f"Failed to save provider: {e!s}"}, status_code=400
        )


@router.post("/setup-all")
async def save_all_providers(req: MultiProviderSetupRequest = Body(...)):
    """
    Save multiple provider API keys to user configuration and reload providers.
    """
    logger.info("Received setup-all request")
    logger.info(f"Request type: {type(req)}")
    logger.info(f"Request attributes: {dir(req)}")

    # Debug: Check if cloudflare_token exists
    if hasattr(req, "cloudflare_token"):
        logger.info(f"cloudflare_token value: {req.cloudflare_token}")
    else:
        logger.error("cloudflare_token attribute missing from request object")
        return JSONResponse(
            {"message": "Request object missing cloudflare_token attribute"},
            status_code=400,
        )

    saved_providers = []
    failed_providers = []

    try:
        logger.info("Starting provider configuration save process")

        # Save OpenAI key if provided
        if req.openai_key:
            try:
                logger.info(f"Saving OpenAI key: {req.openai_key[:10]}...")
                app_state.save_user_config("openai", req.openai_key)
                saved_providers.append("OpenAI")
                logger.info("OpenAI key saved successfully")
            except Exception as e:
                logger.error(f"Failed to save OpenAI key: {e!s}")
                failed_providers.append(f"OpenAI: {e!s}")

        # Save Anthropic key if provided
        if req.anthropic_key:
            try:
                logger.info(f"Saving Anthropic key: {req.anthropic_key[:10]}...")
                app_state.save_user_config("anthropic", req.anthropic_key)
                saved_providers.append("Anthropic")
                logger.info("Anthropic key saved successfully")
            except Exception as e:
                logger.error(f"Failed to save Anthropic key: {e!s}")
                failed_providers.append(f"Anthropic: {e!s}")

        # Save Grok key if provided
        if req.grok_key:
            try:
                logger.info(f"Saving Grok key: {req.grok_key[:10]}...")
                app_state.save_user_config("grok", req.grok_key)
                saved_providers.append("Grok")
                logger.info("Grok key saved successfully")
            except Exception as e:
                logger.error(f"Failed to save Grok key: {e!s}")
                failed_providers.append(f"Grok: {e!s}")

        # Save Cloudflare configuration if provided
        if req.cloudflare_token and req.cloudflare_account:
            try:
                logger.info(f"Saving Cloudflare token: {req.cloudflare_token[:10]}...")
                logger.info(f"Saving Cloudflare account: {req.cloudflare_account}")
                app_state.save_user_config("cloudflare", req.cloudflare_token)
                # Set environment variable for account ID (this would need to persist somehow)
                os.environ["CLOUDFLARE_ACCOUNT_ID"] = req.cloudflare_account
                saved_providers.append("Cloudflare")
                logger.info("Cloudflare configuration saved successfully")
            except Exception as e:
                logger.error(f"Failed to save Cloudflare configuration: {e!s}")
                failed_providers.append(f"Cloudflare: {e!s}")

        logger.info(f"Providers saved: {saved_providers}")
        logger.info(f"Providers failed: {failed_providers}")

        # Reinitialize providers after saving all keys
        logger.info("Reinitializing providers...")
        await app_state.initialize_providers()
        logger.info("Providers reinitialized successfully")

        response_message = f"Successfully configured: {', '.join(saved_providers)}"
        if failed_providers:
            response_message += f". Failed: {', '.join(failed_providers)}"

        logger.info(f"Response message: {response_message}")
        return JSONResponse({"message": response_message})

    except Exception as e:
        logger.exception("Failed to save provider configurations")
        return JSONResponse(
            {"message": f"Failed to save configurations: {e!s}"}, status_code=400
        )
