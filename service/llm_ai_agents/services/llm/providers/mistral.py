import os
from typing import Any, Dict, Iterator
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage
from services.llm.base.llm import BaseLLM


class MistralProvider(BaseLLM):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        model_cfg = config.get("model", {})
        self._client = ChatMistralAI(
            model=model_cfg.get("id", "mistral-large-latest"),
            api_key=os.getenv("MISTRAL_API_KEY"),
            temperature=model_cfg.get("parameters", {}).get("temperature", 0.7),
            max_tokens=model_cfg.get("parameters", {}).get("max_tokens", 512),
        )

    def generate(self, prompt: str, **kwargs) -> str:
        return self._client.invoke([HumanMessage(content=prompt)]).content

    def stream_generate(self, prompt: str, **kwargs) -> Iterator[str]:
        for chunk in self._client.stream([HumanMessage(content=prompt)]):
            yield chunk.content

    async def generate_async(self, prompt: str, **kwargs) -> str:
        result = await self._client.ainvoke([HumanMessage(content=prompt)])
        return result.content

    async def astream_generate(self, prompt: str, **kwargs):
        async for chunk in self._client.astream([HumanMessage(content=prompt)]):
            yield chunk.content

    def get_langchain_model(self) -> Any:
        return self._client
