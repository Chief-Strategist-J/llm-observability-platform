from typing import Any, Dict, Iterator, List
from services.llm.base.llm import BaseLLM


class FakeLLM(BaseLLM):
    def __init__(self, response: str = "fake-response", config: Dict[str, Any] = None):
        super().__init__(config or {"model": {"id": "fake-model", "provider": "fake"}})
        self._response = response
        self.generate_calls: List[str] = []
        self.stream_calls: List[str] = []

    def generate(self, prompt: str, **kwargs) -> str:
        self.generate_calls.append(prompt)
        return self._response

    def stream_generate(self, prompt: str, **kwargs) -> Iterator[str]:
        self.stream_calls.append(prompt)
        for token in self._response.split():
            yield token

    async def generate_async(self, prompt: str, **kwargs) -> str:
        return self._response

    async def astream_generate(self, prompt: str, **kwargs):
        for token in self._response.split():
            yield token

    def get_langchain_model(self) -> Any:
        from unittest.mock import MagicMock
        return MagicMock()
