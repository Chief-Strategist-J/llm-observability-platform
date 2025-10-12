"""Abstract LLM provider interface for the AI Proxy Service.

Defines the contract that all LLM providers must implement to be used within the
service. This allows the system to interact with different LLMs in a consistent way.

"""

from abc import ABC, abstractmethod

from ..domain.models import LLMResponse


class LLMProviderPort(ABC):
    """Abstract base class for all LLM provider implementations.

    Classes implementing this interface must provide an asynchronous `generate`
    method that produces an LLMResponse from a text prompt.

    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """Generate text from a prompt using the LLM provider.

        Args:
            prompt (str): Input text prompt for the LLM.
            max_tokens (int): Maximum number of tokens to generate.
            temperature (float): Sampling temperature controlling randomness.

        Returns:
            LLMResponse: Object containing generated text, provider, and model.

        """
