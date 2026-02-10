from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any


class BaseModelAdapter(ABC):
    @abstractmethod
    async def download_model(self, model_name: str) -> bool:
        pass

    @abstractmethod
    async def delete_model(self, model_name: str) -> bool:
        pass

    @abstractmethod
    async def generate_response(
        self, model_name: str, prompt: str, **kwargs
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def generate_stream(
        self, model_name: str, prompt: str, **kwargs
    ) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def list_models(self) -> list:
        pass

    @abstractmethod
    async def get_model_status(self, model_name: str) -> Dict[str, Any]:
        pass
