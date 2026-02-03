import os
from typing import Optional


class MongoDBConfig:
    URI: str = os.getenv("MONGODB_URI", "mongodb://admin:MongoPassword123!@172.30.0.20:27017/")
    DATABASE: str = os.getenv("MONGODB_DATABASE", "llm_admin")
    MODELS_COLLECTION: str = "ai_models"
    ENDPOINTS_COLLECTION: str = "api_endpoints"


class ApicurioConfig:
    BASE_URL: str = os.getenv("APICURIO_URL", "http://172.29.0.50:8080")
    API_VERSION: str = "v2"
    GROUP_ID: str = "llm-admin"


class OllamaConfig:
    HOST: str = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    TIMEOUT: int = 300


class OpenAIConfig:
    API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    TIMEOUT: int = 60


class AnthropicConfig:
    API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    BASE_URL: str = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1")
    TIMEOUT: int = 60


class ServiceConfig:
    HOST: str = os.getenv("SERVICE_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("SERVICE_PORT", "8100"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    KEEP_ALIVE_DURATION: int = 300


class StreamlitConfig:
    HOST: str = os.getenv("STREAMLIT_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("STREAMLIT_PORT", "8501"))
    THEME: str = "dark"


class ObservabilityConfig:
    OTLP_ENDPOINT: str = os.getenv("OTLP_ENDPOINT", "http://172.28.0.10:4317")
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "llm-model-service")


def get_provider_config(provider: str) -> dict:
    provider_configs = {
        "ollama": {
            "base_url": OllamaConfig.HOST,
            "timeout": OllamaConfig.TIMEOUT,
            "api_key": None
        },
        "openai": {
            "base_url": OpenAIConfig.BASE_URL,
            "timeout": OpenAIConfig.TIMEOUT,
            "api_key": OpenAIConfig.API_KEY
        },
        "anthropic": {
            "base_url": AnthropicConfig.BASE_URL,
            "timeout": AnthropicConfig.TIMEOUT,
            "api_key": AnthropicConfig.API_KEY
        }
    }
    return provider_configs.get(provider, {})
