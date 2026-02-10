import httpx
import json
from typing import AsyncGenerator, Dict, Any, Optional
from config.settings import OLLAMA_HOST
from telemetry.logger import log_event, get_tracer, trace_with_details
from .base import BaseModelAdapter


class OllamaAdapter(BaseModelAdapter):
    def __init__(self):
        self.base_url = OLLAMA_HOST
        log_event("ollama_adapter_init", host=self.base_url)

    @trace_with_details(get_tracer())
    async def _make_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> httpx.Response:
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=300.0) as client:
            if method == "GET":
                response = await client.get(url)
            elif method == "POST":
                response = await client.post(url, json=data)
            elif method == "DELETE":
                response = await client.delete(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            return response

    @trace_with_details(get_tracer())
    async def download_model(self, model_name: str) -> bool:
        log_event("model_download_start", model=model_name)
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/pull",
                    json={"name": model_name},
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            if "error" in data:
                                log_event(
                                    "model_download_error",
                                    model=model_name,
                                    error=data["error"],
                                )
                                return False
                            if data.get("status") == "success":
                                log_event(
                                    "model_download_success", model=model_name
                                )
                                return True
            return True
        except Exception as e:
            log_event(
                "model_download_exception", model=model_name, error=str(e)
            )
            raise

    @trace_with_details(get_tracer())
    async def delete_model(self, model_name: str) -> bool:
        log_event("model_delete_start", model=model_name)
        response = await self._make_request(
            "DELETE", "/api/delete", {"name": model_name}
        )
        if response.status_code == 200:
            log_event("model_delete_success", model=model_name)
            return True
        log_event(
            "model_delete_failed",
            model=model_name,
            status=response.status_code,
        )
        return False

    @trace_with_details(get_tracer())
    async def list_models(self) -> list:
        response = await self._make_request("GET", "/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [m["name"].split(":")[0] for m in models]
        return []

    @trace_with_details(get_tracer())
    async def get_model_status(self, model_name: str) -> Dict[str, Any]:
        current_models = await self.list_models()
        is_downloaded = (
            model_name in current_models
            or f"{model_name}:latest" in current_models
        )
        return {
            "name": model_name,
            "status": "available" if is_downloaded else "not_found",
            "backend": "ollama",
        }

    @trace_with_details(get_tracer())
    async def generate_response(
        self, model_name: str, prompt: str, **kwargs
    ) -> Dict[str, Any]:
        log_event("generate_response_start", model=model_name)
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            **kwargs,
        }
        response = await self._make_request("POST", "/api/generate", payload)
        if response.status_code == 200:
            result = response.json()
            log_event("generate_response_success", model=model_name)
            return {
                "response": result.get("response"),
                "done": True,
                "context": result.get("context"),
            }
        log_event(
            "generate_response_failed",
            model=model_name,
            status=response.status_code,
        )
        return {"error": f"Ollama API Error: {response.status_code}"}

    @trace_with_details(get_tracer())
    async def generate_stream(
        self, model_name: str, prompt: str, **kwargs
    ) -> AsyncGenerator[str, None]:
        log_event("generate_stream_start", model=model_name)
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": True,
            **kwargs,
        }
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=payload,
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done"):
                            log_event(
                                "generate_stream_complete", model=model_name
                            )
