from typing import AsyncGenerator
from .base import BaseAgent, AgentCapability, AgentInput, AgentOutput
from telemetry.logger import log_event


class VoiceAgent(BaseAgent):
    """
    Voice agent — stub for future voice-based AI agent capabilities.

    This will eventually handle:
    - Speech-to-text (STT) input processing
    - LLM inference
    - Text-to-speech (TTS) output synthesis
    - Real-time audio streaming via WebSocket

    For now, it serves as the extension point and declares voice capability
    in the agent registry so the dashboard can show it as "coming soon".
    """

    def __init__(self, agent_id: str = "voice"):
        super().__init__(agent_id)
        log_event("voice_agent_init", agent_id=agent_id, status="stub")

    async def execute(self, input: AgentInput) -> AgentOutput:
        raise NotImplementedError(
            "VoiceAgent is not yet implemented. "
            "This is a planned extension for real-time voice interactions."
        )

    async def stream(self, input: AgentInput) -> AsyncGenerator[str, None]:
        raise NotImplementedError(
            "VoiceAgent streaming is not yet implemented."
        )
        yield  # pragma: no cover — makes this a valid async generator

    def get_capabilities(self) -> AgentCapability:
        return AgentCapability(
            name="voice",
            supports_streaming=True,
            supports_voice=True,
            supported_models=[],
            metadata={"status": "coming_soon"},
        )
