from ..domain.models import LLMRequest, LLMResponse
from ..ports.llm_provider import LLMProviderPort


async def generate_text(
    request: LLMRequest,
    provider: LLMProviderPort,
    default_max_tokens: int,
    default_temperature: float,
) -> LLMResponse:
    return await provider.generate(
        prompt=request.prompt,
        max_tokens=request.max_tokens or default_max_tokens,
        temperature=request.temperature or default_temperature,
    )
