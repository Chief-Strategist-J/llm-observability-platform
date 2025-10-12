from ..domain.models import STTRequest, STTResponse
from ..ports.stt_provider import STTProviderPort


async def transcribe_audio(
    request: STTRequest, provider: STTProviderPort
) -> STTResponse:
    return await provider.transcribe(request.audio_data)
