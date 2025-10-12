"""Abstract TTS (Text-to-Speech) provider interface for the AI Proxy Service.

Defines the contract that all TTS providers must implement. This ensures that the
service can interact with different TTS providers in a consistent manner.

"""

from abc import ABC, abstractmethod

from ..domain.models import TTSResponse


class TTSProviderPort(ABC):
    """Abstract base class for all TTS provider implementations.

    Classes implementing this interface must provide an asynchronous `synthesize`
    method that produces a TTSResponse from input text.

    """

    @abstractmethod
    async def synthesize(self, text: str) -> TTSResponse:
        """Synthesize input text to speech.

        Args:
            text (str): Input text to be converted to speech.

        Returns:
            TTSResponse: Object containing the synthesized audio and metadata.

        """
