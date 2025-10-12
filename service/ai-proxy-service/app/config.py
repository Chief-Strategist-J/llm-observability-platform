"""Application state module for AI Proxy Service.

Defines the central singleton `AppState` which holds service configuration and
initialized LLM provider instances. Responsible for loading configuration from
providers.yaml and initializing all enabled LLM providers.

"""

import logging
import os
import sys

import yaml

from ..adapters.llm_provider.anthropic import AnthropicLLM
from ..adapters.llm_provider.cloudflare import CloudflareLLM
from ..adapters.llm_provider.grok import GrokLLM
from ..adapters.llm_provider.openai import OpenAILLM

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class AppState:
    """Central configuration and provider initialization holder for the AI Proxy
    service.

    Attributes:
        config (Dict): Loaded configuration dictionary from providers.yaml.
        llm_providers (Dict[str, object]): Dictionary of initialized LLM provider instances.

    """

    def __init__(self):
        self.config: dict = {}
        self.llm_providers: dict[str, object] = {}

    def load_config(self):
        """
        Loads configuration from providers.yaml into self.config.
        """
        config_path = os.getenv(
            "CONFIG_PATH", "/app/service/ai-proxy-service/config/providers.yaml"
        )
        with open(config_path, encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        logger.debug("Configuration loaded: %s", self.config)

    async def initialize_providers(self):
        """Initializes all enabled LLM providers based on configuration and environment
        variables.

        Populates self.llm_providers with provider instances.

        """
        llm_config = self.config.get("llm", {})

        if llm_config.get("cloudflare", {}).get("enabled"):
            cf_account = os.getenv("CLOUDFLARE_ACCOUNT_ID")
            cf_token = os.getenv("CLOUDFLARE_API_TOKEN")
            if cf_account and cf_token:
                self.llm_providers["cloudflare"] = CloudflareLLM(
                    account_id=cf_account,
                    api_token=cf_token,
                    model=llm_config["cloudflare"]["model"],
                )
                logger.info("Cloudflare LLM enabled")
            else:
                logger.warning(
                    "Cloudflare credentials missing; provider not initialized"
                )

        if llm_config.get("openai", {}).get("enabled"):
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                self.llm_providers["openai"] = OpenAILLM(
                    api_key=openai_key, model=llm_config["openai"]["model"]
                )
                logger.info("OpenAI LLM enabled")
            else:
                logger.warning("OpenAI API key missing; provider not initialized")

        if llm_config.get("grok", {}).get("enabled"):
            grok_key = os.getenv("GROK_API_KEY")
            if grok_key:
                self.llm_providers["grok"] = GrokLLM(
                    api_key=grok_key,
                    model=llm_config["grok"]["model"],
                    base_url=llm_config["grok"]["base_url"],
                )
                logger.info("Grok LLM enabled")
            else:
                logger.warning("Grok API key missing; provider not initialized")

        if llm_config.get("anthropic", {}).get("enabled"):
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            if anthropic_key:
                self.llm_providers["anthropic"] = AnthropicLLM(
                    api_key=anthropic_key, model=llm_config["anthropic"]["model"]
                )
                logger.info("Anthropic LLM enabled")
            else:
                logger.warning("Anthropic API key missing; provider not initialized")

        if not self.llm_providers:
            logger.warning("No LLM providers configured")


app_state = AppState()
