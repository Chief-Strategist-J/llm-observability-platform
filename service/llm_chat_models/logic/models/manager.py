from typing import List, Dict, Any
from .registry import get_model_info, SUPPORTED_MODELS
from .adapters.base import BaseModelAdapter
from .adapters.ollama import OllamaAdapter
from telemetry.logger import log_event, get_tracer, trace_with_details


class ModelManager:
    def __init__(self):
        self.adapter: BaseModelAdapter = OllamaAdapter()
        log_event("model_manager_init", backend="ollama")

    @trace_with_details(get_tracer())
    async def list_available_models(self) -> List[Dict[str, Any]]:
        available = []
        downloaded_names = await self.adapter.list_models()

        for model_id, info in SUPPORTED_MODELS.items():
            model_data = info.copy()
            model_data["downloaded"] = info["name"] in downloaded_names
            available.append(model_data)
        return available

    @trace_with_details(get_tracer())
    async def get_model_status(self, model_name: str) -> Dict[str, Any]:
        info = get_model_info(model_name)
        if not info:
            return {"status": "unknown_model", "name": model_name}

        status = await self.adapter.get_model_status(info["name"])
        return {**info, **status}

    @trace_with_details(get_tracer())
    async def download_model(self, model_name: str) -> bool:
        info = get_model_info(model_name)
        if not info:
            log_event(
                "download_model_failed",
                reason="unknown_model",
                model=model_name,
            )
            raise ValueError(f"Unknown model: {model_name}")

        repo_name = info["name"]
        log_event("manager_download_start", model=model_name, repo=repo_name)
        return await self.adapter.download_model(repo_name)

    @trace_with_details(get_tracer())
    async def start_model(self, model_name: str) -> bool:
        info = get_model_info(model_name)
        if not info:
            raise ValueError(f"Unknown model: {model_name}")

        status = await self.adapter.get_model_status(info["name"])
        if status.get("status") != "available":
            log_event(
                "start_model_failed",
                reason="not_downloaded",
                model=model_name,
            )
            return False

        log_event("manager_start_model", model=model_name)
        return True

    @trace_with_details(get_tracer())
    async def stop_model(self, model_name: str) -> bool:
        log_event("manager_stop_model", model=model_name)
        return True

    @trace_with_details(get_tracer())
    async def delete_model(self, model_name: str) -> bool:
        info = get_model_info(model_name)
        if not info:
            raise ValueError(f"Unknown model: {model_name}")

        repo_name = info["name"]
        log_event("manager_delete_model", model=model_name)
        return await self.adapter.delete_model(repo_name)

    @trace_with_details(get_tracer())
    async def generate_response(
        self, model_name: str, prompt: str, **kwargs
    ) -> Dict[str, Any]:
        info = get_model_info(model_name)
        if not info:
            raise ValueError(f"Unknown model: {model_name}")

        return await self.adapter.generate_response(
            info["name"], prompt, **kwargs
        )

    @trace_with_details(get_tracer())
    async def generate_stream(self, model_name: str, prompt: str, **kwargs):
        info = get_model_info(model_name)
        if not info:
            raise ValueError(f"Unknown model: {model_name}")

        async for chunk in self.adapter.generate_stream(
            info["name"], prompt, **kwargs
        ):
            yield chunk
