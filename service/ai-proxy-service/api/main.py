"""AI Proxy Service API.

This module provides a FastAPI-based REST API for the AI Proxy service, which acts as a
gateway to multiple LLM providers.

"""

import logging
import os
import sys

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yaml

from ..adapters.llm_provider.anthropic import AnthropicLLM
from ..adapters.llm_provider.cloudflare import CloudflareLLM
from ..adapters.llm_provider.grok import GrokLLM
from ..adapters.llm_provider.openai import OpenAILLM
from ..core.domain.models import LLMRequest
from ..core.usecases.generate_text import generate_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Proxy")

CONFIG = {}
LLM_PROVIDERS: dict = {}


@app.on_event("startup")
async def startup():
    """
    Initialize the AI Proxy service on startup.
    """
    global CONFIG, LLM_PROVIDERS

    with open("config/providers.yaml") as f:
        CONFIG = yaml.safe_load(f)

    llm_config = CONFIG["llm"]

    if llm_config.get("cloudflare", {}).get("enabled"):
        cf_account = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        cf_token = os.getenv("CLOUDFLARE_API_TOKEN")
        if cf_account and cf_token:
            LLM_PROVIDERS["cloudflare"] = CloudflareLLM(
                account_id=cf_account,
                api_token=cf_token,
                model=llm_config["cloudflare"]["model"],
            )
            logger.info("Cloudflare LLM enabled")

    if llm_config.get("openai", {}).get("enabled"):
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            LLM_PROVIDERS["openai"] = OpenAILLM(
                api_key=openai_key, model=llm_config["openai"]["model"]
            )
            logger.info("OpenAI LLM enabled")

    if llm_config.get("grok", {}).get("enabled"):
        grok_key = os.getenv("GROK_API_KEY")
        if grok_key:
            LLM_PROVIDERS["grok"] = GrokLLM(
                api_key=grok_key,
                model=llm_config["grok"]["model"],
                base_url=llm_config["grok"]["base_url"],
            )
            logger.info("Grok LLM enabled")

    if llm_config.get("anthropic", {}).get("enabled"):
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            LLM_PROVIDERS["anthropic"] = AnthropicLLM(
                api_key=anthropic_key, model=llm_config["anthropic"]["model"]
            )
            logger.info("Anthropic LLM enabled")

    if not LLM_PROVIDERS:
        logger.warning("No LLM providers configured")


@app.get("/health")
async def health():
    """
    Get the health status of the AI Proxy service.
    """
    return {
        "status": "ok",
        "providers": list(LLM_PROVIDERS.keys()),
        "default": CONFIG["llm"]["default"],
    }


class GenerateRequest(BaseModel):
    prompt: str
    provider: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None


@app.post("/generate")
async def generate(req: GenerateRequest):
    """
    Generate text using the specified LLM provider.
    """
    provider_name = req.provider or CONFIG["llm"]["default"]

    if provider_name not in LLM_PROVIDERS:
        raise HTTPException(400, f"Provider '{provider_name}' not available")

    provider = LLM_PROVIDERS[provider_name]
    provider_config = CONFIG["llm"][provider_name]

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
            provider_config["max_tokens"],
            provider_config["temperature"],
        )
        return {
            "text": response.text,
            "provider": response.provider,
            "model": response.model,
        }
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(500, str(e)) from e
