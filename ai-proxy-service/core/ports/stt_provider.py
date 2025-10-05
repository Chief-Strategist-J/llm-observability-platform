from abc import ABC, abstractmethod
from core.domain.models import STTResponse

class STTProviderPort(ABC):
    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> STTResponse:
        pass
