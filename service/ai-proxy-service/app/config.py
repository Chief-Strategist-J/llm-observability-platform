"""Configuration module for the AI Proxy service.

This module provides configuration management for the AI Proxy service, including:
- Provider configuration models for different LLM services
- User configuration for API keys
- Application state management
- Provider initialization and management

The module uses Pydantic models for type-safe configuration and supports
loading configuration from YAML files and user-provided API keys.

"""

import json
import logging
import os
import sys

from pydantic import BaseModel
import yaml

from ..adapters.llm_provider.anthropic import AnthropicLLM
from ..adapters.llm_provider.cloudflare import CloudflareLLM
from ..adapters.llm_provider.grok import GrokLLM
from ..adapters.llm_provider.openai import OpenAILLM

# Configure logging for the configuration module
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Logger instance for this module
logger = logging.getLogger(__name__)


class LLMUserConfig(BaseModel):
    """Configuration model for storing API keys for different LLM providers.

    This model holds optional API keys for various Large Language Model providers
    that can be used by the AI Proxy service. Each field represents a specific
    provider and can be None if no API key is configured for that provider.

    Attributes:
        openai (Optional[str]): OpenAI API key for GPT models
        anthropic (Optional[str]): Anthropic API key for Claude models
        grok (Optional[str]): Grok API key for xAI models
        cloudflare (Optional[str]): Cloudflare API token for Workers AI

    """

    openai: str | None = None
    anthropic: str | None = None
    grok: str | None = None
    cloudflare: str | None = None


class UserConfig(BaseModel):
    """Main user configuration model for the AI Proxy service.

    This model encapsulates all user-configurable settings for the AI Proxy service,
    with the primary configuration being LLM provider API keys stored in the
    nested LLMUserConfig model.

    Attributes:
        llm (LLMUserConfig): Nested configuration for LLM provider API keys

    """

    llm: LLMUserConfig = LLMUserConfig()


class ProviderConfig(BaseModel):
    """Configuration model for individual LLM provider settings.

    This model defines the configuration parameters for a single LLM provider,
    including whether it's enabled, which model to use, and various parameters.

    Attributes:
        enabled (bool): Whether this provider is enabled for use
        model (str): The specific model to use for this provider
        max_tokens (Optional[int]): Maximum tokens per request (default: 256)
        temperature (Optional[float]): Sampling temperature for responses (default: 0.7)
        base_url (Optional[str]): Custom base URL for the provider API

    """

    enabled: bool
    model: str
    max_tokens: int | None = 256
    temperature: float | None = 0.7
    base_url: str | None = None


class LLMConfig(BaseModel):
    """Configuration model for all LLM provider settings.

    This model contains the configuration for all supported LLM providers,
    including the default provider and individual provider configurations.

    Attributes:
        default (str): Name of the default provider to use
        cloudflare (ProviderConfig): Cloudflare Workers AI configuration
        openai (ProviderConfig): OpenAI GPT models configuration
        grok (ProviderConfig): Grok xAI models configuration
        anthropic (ProviderConfig): Anthropic Claude models configuration

    """

    default: str
    cloudflare: ProviderConfig
    openai: ProviderConfig
    grok: ProviderConfig
    anthropic: ProviderConfig


class AppConfig(BaseModel):
    """Main application configuration model.

    This model represents the complete application configuration loaded from
    the providers.yaml file, containing all LLM provider configurations.

    Attributes:
        llm (LLMConfig): Complete LLM configuration including all providers

    """

    llm: LLMConfig


class AppState:
    """Central application state manager for the AI Proxy service.

    This class manages the application configuration, provider initialization,
    and user settings. It serves as the central hub for configuration management
    and provider lifecycle management.

    Attributes:
        config (dict): Raw configuration dictionary loaded from YAML file
        config_model (Optional[AppConfig]): Typed configuration model for validation
        llm_providers (dict[str, object]): Dictionary of initialized LLM provider instances
        user_config_path (str): Path to the user configuration JSON file
        user_config (UserConfig): User configuration containing API keys

    """

    def __init__(self):
        """Initialize the application state with default values.

        Sets up empty configuration, no providers, and default user configuration. The
        user_config_path is constructed relative to this module's location.

        """
        self.config: dict = {}
        self.config_model: AppConfig | None = None
        self.llm_providers: dict[str, object] = {}
        self.user_config_path = os.path.join(
            os.path.dirname(__file__), "../config/user_config.json"
        )
        self.user_config: UserConfig = UserConfig()

    def load_config(self):
        """Load configuration from providers.yaml file.

        Loads the main application configuration from the YAML file specified by the
        CONFIG_PATH environment variable (defaults to a standard path). The
        configuration is loaded both as a raw dictionary and validated against the
        AppConfig Pydantic model. Also triggers loading of user config.

        """
        config_path = os.getenv(
            "CONFIG_PATH", "/app/service/ai-proxy-service/config/providers.yaml"
        )
        with open(config_path, encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self.config_model = AppConfig.model_validate(self.config)
        logger.debug("Configuration loaded: %s", self.config_model)
        self.load_user_config()

    async def initialize_providers(self):
        """Initialize all enabled LLM providers based on configuration.

        Iterates through all configured providers and initializes them if enabled and
        proper credentials are available. Providers are initialized with user-provided
        API keys taking priority over environment variables.

        The method logs the status of each provider initialization attempt.

        """
        llm_config = self.config_model.llm
        user_keys = self.user_config.llm

        if llm_config.cloudflare.enabled:
            model = llm_config.cloudflare.model
            key = user_keys.cloudflare or os.getenv("CLOUDFLARE_API_TOKEN")
            account = os.getenv("CLOUDFLARE_ACCOUNT_ID")
            if key and account:
                self.llm_providers["cloudflare"] = CloudflareLLM(
                    account_id=account,
                    api_token=key,
                    model=model,
                )
                logger.info("Cloudflare LLM enabled")
            else:
                logger.warning(
                    "Cloudflare credentials missing; provider not initialized"
                )

        if llm_config.openai.enabled:
            model = llm_config.openai.model
            key = user_keys.openai or os.getenv("OPENAI_API_KEY")
            if key:
                self.llm_providers["openai"] = OpenAILLM(
                    api_key=key,
                    model=model,
                )
                logger.info("OpenAI LLM enabled")
            else:
                logger.warning("OpenAI API key missing; provider not initialized")

        if llm_config.grok.enabled:
            model = llm_config.grok.model
            base_url = llm_config.grok.base_url
            key = user_keys.grok or os.getenv("GROK_API_KEY")
            if key:
                self.llm_providers["grok"] = GrokLLM(
                    api_key=key,
                    model=model,
                    base_url=base_url,
                )
                logger.info("Grok LLM enabled")
            else:
                logger.warning("Grok API key missing; provider not initialized")

        if llm_config.anthropic.enabled:
            model = llm_config.anthropic.model
            key = user_keys.anthropic or os.getenv("ANTHROPIC_API_KEY")
            if key:
                self.llm_providers["anthropic"] = AnthropicLLM(
                    api_key=key,
                    model=model,
                )
                logger.info("Anthropic LLM enabled")
            else:
                logger.warning("Anthropic API key missing; provider not initialized")

        if not self.llm_providers:
            logger.warning("No LLM providers configured")

    def load_user_config(self):
        """Load user configuration from user_config.json file.

        Attempts to load user-provided API keys from the JSON configuration file. If the
        file doesn't exist, initializes with default empty configuration. The loaded
        data is validated against the UserConfig Pydantic model.

        """
        if os.path.exists(self.user_config_path):
            with open(self.user_config_path, encoding="utf-8") as f:
                data = json.load(f)
                self.user_config = UserConfig.model_validate(data)
            logger.debug("User config loaded: %s", self.user_config)
        else:
            self.user_config = UserConfig()

    def save_user_config(self, provider: str, api_key: str):
        """Save a provider API key to user configuration file.

        Saves the provided API key for the specified provider to the user
        configuration file. The provider must be a valid attribute of the
        LLMUserConfig model, otherwise a warning is logged and no action taken.

        Args:
            provider (str): Name of the provider (e.g., 'openai', 'anthropic')
            api_key (str): The API key to save for the provider

        """
        if not hasattr(self.user_config.llm, provider):
            logger.warning("Unknown provider '%s'; skipping save", provider)
            return

        setattr(self.user_config.llm, provider, api_key)
        os.makedirs(os.path.dirname(self.user_config_path), exist_ok=True)
        with open(self.user_config_path, "w", encoding="utf-8") as f:
            f.write(self.user_config.model_dump_json(indent=2))
        logger.info("Saved API key for provider '%s'", provider)


# Global application state instance
# This is the main AppState instance used throughout the application
# for configuration management and provider access
app_state = AppState()
