from abc import ABC, abstractmethod

from core.domain.models import LLMResponse


class LLMProviderPort(ABC):
    @abstractmethod
    async def generate(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> LLMResponse:
        pass
