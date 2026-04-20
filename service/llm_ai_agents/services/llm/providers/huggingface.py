import os
from typing import Any, Dict, Iterator
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.messages import HumanMessage
from services.llm.base.llm import BaseLLM


class HuggingFaceProvider(BaseLLM):
    """HuggingFace Inference API (cloud). Distinct from local.py (local transformers)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        model_cfg = config.get("model", {})
        self._client = HuggingFaceEndpoint(
            repo_id=model_cfg.get("id", "HuggingFaceH4/zephyr-7b-beta"),
            huggingfacehub_api_token=os.getenv("HF_TOKEN"),
            temperature=model_cfg.get("parameters", {}).get("temperature", 0.7),
            max_new_tokens=model_cfg.get("parameters", {}).get("max_tokens", 512),
        )

    def generate(self, prompt: str, **kwargs) -> str:
        return self._client.invoke(prompt)

    def stream_generate(self, prompt: str, **kwargs) -> Iterator[str]:
        for chunk in self._client.stream(prompt):
            yield chunk

    async def generate_async(self, prompt: str, **kwargs) -> str:
        return await self._client.ainvoke(prompt)

    async def astream_generate(self, prompt: str, **kwargs):
        async for chunk in self._client.astream(prompt):
            yield chunk

    def get_langchain_model(self) -> Any:
        return self._client
