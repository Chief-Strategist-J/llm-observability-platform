from typing import AsyncGenerator
from .base import BaseAgent, AgentCapability, AgentInput, AgentOutput
from logic.models.manager import ModelManager
from logic.models.registry import SUPPORTED_MODELS
from telemetry.logger import log_event


class ChatAgent(BaseAgent):
    """
    Chat agent — wraps LLM model interaction for text-based conversations.

    This is the primary agent type. It delegates to the ModelManager for
    actual inference and exposes the standardized agent interface so the
    gateway and workflow engine can use it uniformly.
    """

    def __init__(self, agent_id: str = "chat"):
        super().__init__(agent_id)
        self.model_manager = ModelManager()
        log_event("chat_agent_init", agent_id=agent_id)

    async def execute(self, input: AgentInput) -> AgentOutput:
        log_event("chat_agent_execute", model=input.model)

        prompt = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in input.messages]
        )

        result = await self.model_manager.generate_response(
            model_name=input.model,
            prompt=prompt,
            temperature=input.temperature,
            max_tokens=input.max_tokens,
        )

        if "error" in result:
            log_event("chat_agent_error", error=result["error"])
            return AgentOutput(
                content="",
                model=input.model,
                finish_reason="error",
                metadata={"error": result["error"]},
            )

        return AgentOutput(
            content=result.get("response", ""),
            model=input.model,
            finish_reason="stop",
        )

    async def stream(self, input: AgentInput) -> AsyncGenerator[str, None]:
        log_event("chat_agent_stream", model=input.model)

        prompt = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in input.messages]
        )

        async for chunk in self.model_manager.generate_stream(
            model_name=input.model,
            prompt=prompt,
            temperature=input.temperature,
            max_tokens=input.max_tokens,
        ):
            yield chunk

    def get_capabilities(self) -> AgentCapability:
        return AgentCapability(
            name="chat",
            supports_streaming=True,
            supports_voice=False,
            supported_models=list(SUPPORTED_MODELS.keys()),
        )
