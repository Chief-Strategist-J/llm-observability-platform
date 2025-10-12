from ..domain.models import TTSRequest, TTSResponse
from ..ports.tts_provider import TTSProviderPort


async def synthesize_speech(
    request: TTSRequest, provider: TTSProviderPort
) -> TTSResponse:
    return await provider.synthesize(request.text)
