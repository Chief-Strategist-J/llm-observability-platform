"""Abstract STT (Speech-to-Text) provider interface for the AI Proxy Service.

Defines the contract that all STT providers must implement. This ensures that the
service can interact with different STT providers in a consistent manner.

"""

from abc import ABC, abstractmethod

from ..domain.models import STTResponse


class STTProviderPort(ABC):
    """Abstract base class for all STT provider implementations.

    Classes implementing this interface must provide an asynchronous `transcribe`
    method that produces an STTResponse from raw audio data.

    """

    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> STTResponse:
        """Transcribe raw audio data to text.

        Args:
            audio_data (bytes): Raw audio bytes to be transcribed.

        Returns:
            STTResponse: Object containing the transcribed text and metadata.

        """
