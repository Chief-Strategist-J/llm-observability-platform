from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import os
import yaml
import logging
import sys

from core.domain.models import LLMRequest
from core.usecases.generate_text import generate_text
from adapters.llm_provider.cloudflare import CloudflareLLM
from adapters.llm_provider.openai import OpenAILLM
from adapters.llm_provider.grok import GrokLLM
from adapters.llm_provider.anthropic import AnthropicLLM

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Proxy")

config = {}
llm_providers: Dict = {}

@app.on_event("startup")
async def startup():
    global config, llm_providers
    
    with open("config/providers.yaml") as f:
        config = yaml.safe_load(f)
    
    llm_config = config["llm"]
    
    if llm_config.get("cloudflare", {}).get("enabled"):
        cf_account = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        cf_token = os.getenv("CLOUDFLARE_API_TOKEN")
        if cf_account and cf_token:
            llm_providers["cloudflare"] = CloudflareLLM(
                account_id=cf_account,
                api_token=cf_token,
                model=llm_config["cloudflare"]["model"]
            )
            logger.info("Cloudflare LLM enabled")
    
    if llm_config.get("openai", {}).get("enabled"):
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            llm_providers["openai"] = OpenAILLM(
                api_key=openai_key,
                model=llm_config["openai"]["model"]
            )
            logger.info("OpenAI LLM enabled")
    
    if llm_config.get("grok", {}).get("enabled"):
        grok_key = os.getenv("GROK_API_KEY")
        if grok_key:
            llm_providers["grok"] = GrokLLM(
                api_key=grok_key,
                model=llm_config["grok"]["model"],
                base_url=llm_config["grok"]["base_url"]
            )
            logger.info("Grok LLM enabled")
    
    if llm_config.get("anthropic", {}).get("enabled"):
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            llm_providers["anthropic"] = AnthropicLLM(
                api_key=anthropic_key,
                model=llm_config["anthropic"]["model"]
            )
            logger.info("Anthropic LLM enabled")
    
    if not llm_providers:
        logger.warning("No LLM providers configured")

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "providers": list(llm_providers.keys()),
        "default": config["llm"]["default"]
    }

class GenerateRequest(BaseModel):
    prompt: str
    provider: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

@app.post("/generate")
async def generate(req: GenerateRequest):
    provider_name = req.provider or config["llm"]["default"]
    
    if provider_name not in llm_providers:
        raise HTTPException(400, f"Provider '{provider_name}' not available")
    
    provider = llm_providers[provider_name]
    provider_config = config["llm"][provider_name]
    
    request = LLMRequest(
        prompt=req.prompt,
        provider=provider_name,
        max_tokens=req.max_tokens,
        temperature=req.temperature
    )
    
    try:
        response = await generate_text(
            request,
            provider,
            provider_config["max_tokens"],
            provider_config["temperature"]
        )
        return {
            "text": response.text,
            "provider": response.provider,
            "model": response.model
        }
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(500, str(e))
