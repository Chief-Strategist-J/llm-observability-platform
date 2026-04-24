from typing import Dict, Type
from services.llm.base.llm import BaseLLM
from services.llm.providers.local import LocalLLMProvider
from services.llm.providers.openai import OpenAIProvider
from services.llm.providers.anthropic import AnthropicProvider
from services.llm.providers.gemini import GeminiProvider
from services.llm.providers.grok import GrokProvider
from services.llm.providers.mistral import MistralProvider
from services.llm.providers.huggingface import HuggingFaceProvider
from services.llm.providers.cloudflare import CloudflareWorkersAIProvider

PROVIDER_REGISTRY: Dict[str, Type[BaseLLM]] = {
    "local": LocalLLMProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "grok": GrokProvider,
    "mistral": MistralProvider,
    "huggingface": HuggingFaceProvider,
    "cloudflare": CloudflareWorkersAIProvider,
}
