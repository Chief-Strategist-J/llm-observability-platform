import os
from typing import Any, Dict, Iterator

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from services.llm.base.llm import BaseLLM

_DEFAULT_CF_BASE = 'https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1'


class CloudflareWorkersAIProvider(BaseLLM):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        model_cfg = config.get('model', {})

        api_token = os.getenv('CLOUDFLARE_API_TOKEN', '').strip()
        if not api_token:
            raise ValueError('CLOUDFLARE_API_TOKEN is required for cloudflare provider')

        account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID', '').strip()
        configured_base_url = os.getenv('CLOUDFLARE_BASE_URL', '').strip()
        if not configured_base_url and not account_id:
            raise ValueError('CLOUDFLARE_ACCOUNT_ID is required when CLOUDFLARE_BASE_URL is not set')

        base_url = (configured_base_url or _DEFAULT_CF_BASE.format(account_id=account_id)).rstrip('/')

        model_id = model_cfg.get('id', '@cf/meta/llama-3.1-8b-instruct')
        if not str(model_id).strip():
            raise ValueError('Cloudflare model id cannot be empty')

        self._client = ChatOpenAI(
            model=model_id,
            api_key=api_token,
            base_url=base_url,
            temperature=model_cfg.get('parameters', {}).get('temperature', 0.7),
            max_tokens=model_cfg.get('parameters', {}).get('max_tokens', 512),
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
