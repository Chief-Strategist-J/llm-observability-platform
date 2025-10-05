from abc import ABC, abstractmethod
from core.domain.models import TTSResponse

class TTSProviderPort(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> TTSResponse:
        pass
