import logging
import time
import httpx
from typing import Dict, Any, Optional, List

from infrastructure.observability.scripts.observability_client import ObservabilityClient, trace_with_details
from ..data.model_repository import model_repository
from ..data.endpoint_repository import endpoint_repository
from ..data.schemas import ProviderType

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

obs = ObservabilityClient(service_name="request-handler")
tracer = obs.tracer


class RequestHandler:
    def __init__(self):
        logger.info("event=request_handler_init")

    @trace_with_details(tracer)
    async def execute_request(self, endpoint_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        logger.info("event=execute_request_start endpoint_id=%s", endpoint_id)
        endpoint = endpoint_repository.get_endpoint_by_id(endpoint_id)
        if not endpoint:
            logger.error("event=execute_request_error reason=endpoint_not_found endpoint_id=%s", endpoint_id)
            return {"success": False, "error": "Endpoint not found"}
        if not endpoint.get("is_active"):
            logger.error("event=execute_request_error reason=endpoint_inactive endpoint_id=%s", endpoint_id)
            return {"success": False, "error": "Endpoint is not active"}
        model = model_repository.get_model_by_id(endpoint["model_id"])
        if not model:
            logger.error("event=execute_request_error reason=model_not_found model_id=%s", endpoint["model_id"])
            return {"success": False, "error": "Model not found"}
        if not model.get("is_active"):
            logger.error("event=execute_request_error reason=model_inactive model_id=%s", endpoint["model_id"])
            return {"success": False, "error": "Model is not active"}
        try:
            payload = self._build_request(model, endpoint, request_data)
            url = self._get_request_url(model)
            headers = self._get_request_headers(model)
            response = await self._make_request(url, "POST", headers, payload, model.get("timeout", 300))
            mapped_response = self._map_response(response, endpoint.get("response_mapping", {}))
            latency_ms = (time.time() - start_time) * 1000
            logger.info("event=execute_request_success endpoint_id=%s latency_ms=%.2f", endpoint_id, latency_ms)
            obs.record_histogram("request_handler.latency", latency_ms, {"endpoint": endpoint["name"], "status": "success"})
            return {
                "success": True,
                "endpoint_name": endpoint["name"],
                "model_name": model["name"],
                "response": mapped_response,
                "latency_ms": latency_ms
            }
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error("event=execute_request_error endpoint_id=%s error=%s latency_ms=%.2f", endpoint_id, str(e), latency_ms)
            obs.record_histogram("request_handler.latency", latency_ms, {"endpoint": endpoint["name"], "status": "error"})
            obs.log_error(f"execute_request failed: {e}")
            return {"success": False, "error": str(e)}

    @trace_with_details(tracer)
    async def execute_by_path(self, endpoint_path: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("event=execute_by_path_start path=%s", endpoint_path)
        endpoint = endpoint_repository.get_endpoint_by_path(endpoint_path)
        if not endpoint:
            logger.error("event=execute_by_path_error reason=endpoint_not_found path=%s", endpoint_path)
            return {"success": False, "error": f"Endpoint not found: {endpoint_path}"}
        return await self.execute_request(endpoint["_id"], request_data)

    @trace_with_details(tracer)
    async def test_model(self, model_id: str, prompt: str, system_prompt: Optional[str] = None, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> Dict[str, Any]:
        start_time = time.time()
        logger.info("event=test_model_start model_id=%s", model_id)
        model = model_repository.get_model_by_id(model_id)
        if not model:
            logger.error("event=test_model_error reason=model_not_found model_id=%s", model_id)
            return {"success": False, "error": "Model not found", "model_name": "", "latency_ms": 0}
        try:
            payload = self._build_test_payload(model, prompt, system_prompt, temperature, max_tokens)
            url = self._get_request_url(model)
            headers = self._get_request_headers(model)
            response = await self._make_request(url, "POST", headers, payload, model.get("timeout", 300))
            content = self._extract_response_content(response, model["provider"])
            latency_ms = (time.time() - start_time) * 1000
            logger.info("event=test_model_success model_id=%s latency_ms=%.2f", model_id, latency_ms)
            obs.record_histogram("request_handler.test_latency", latency_ms, {"model": model["name"], "status": "success"})
            return {
                "success": True,
                "model_name": model["name"],
                "response": content,
                "latency_ms": latency_ms
            }
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error("event=test_model_error model_id=%s error=%s latency_ms=%.2f", model_id, str(e), latency_ms)
            obs.record_histogram("request_handler.test_latency", latency_ms, {"model": model["name"], "status": "error"})
            return {
                "success": False,
                "model_name": model["name"],
                "error": str(e),
                "latency_ms": latency_ms
            }

    def _build_request(self, model: Dict[str, Any], endpoint: Dict[str, Any], request_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("event=build_request provider=%s", model["provider"])
        provider = model["provider"]
        template = endpoint.get("request_template", {})
        prompt_field = template.get("prompt_field", "prompt")
        prompt = request_data.get(prompt_field, request_data.get("prompt", ""))
        system_prompt = template.get("system_prompt") or request_data.get("system_prompt")
        if provider == ProviderType.OLLAMA.value:
            payload = {
                "model": model["model_id"],
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": model.get("temperature", 0.7),
                    "num_predict": model.get("max_tokens", 2048)
                }
            }
            if system_prompt:
                payload["system"] = system_prompt
            return payload
        elif provider == ProviderType.OPENAI.value:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            return {
                "model": model["model_id"],
                "messages": messages,
                "temperature": model.get("temperature", 0.7),
                "max_tokens": model.get("max_tokens", 2048)
            }
        elif provider == ProviderType.ANTHROPIC.value:
            return {
                "model": model["model_id"],
                "messages": [{"role": "user", "content": prompt}],
                "system": system_prompt or "",
                "max_tokens": model.get("max_tokens", 2048),
                "temperature": model.get("temperature", 0.7)
            }
        else:
            payload = {"prompt": prompt}
            if system_prompt:
                payload["system_prompt"] = system_prompt
            payload.update(request_data)
            return payload

    def _build_test_payload(self, model: Dict[str, Any], prompt: str, system_prompt: Optional[str], temperature: Optional[float], max_tokens: Optional[int]) -> Dict[str, Any]:
        logger.info("event=build_test_payload provider=%s", model["provider"])
        provider = model["provider"]
        temp = temperature if temperature is not None else model.get("temperature", 0.7)
        tokens = max_tokens if max_tokens is not None else model.get("max_tokens", 2048)
        if provider == ProviderType.OLLAMA.value:
            payload = {
                "model": model["model_id"],
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temp, "num_predict": tokens}
            }
            if system_prompt:
                payload["system"] = system_prompt
            return payload
        elif provider == ProviderType.OPENAI.value:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            return {"model": model["model_id"], "messages": messages, "temperature": temp, "max_tokens": tokens}
        elif provider == ProviderType.ANTHROPIC.value:
            return {
                "model": model["model_id"],
                "messages": [{"role": "user", "content": prompt}],
                "system": system_prompt or "",
                "max_tokens": tokens,
                "temperature": temp
            }
        else:
            return {"prompt": prompt, "temperature": temp, "max_tokens": tokens}

    def _get_request_url(self, model: Dict[str, Any]) -> str:
        provider = model["provider"]
        base_url = model["base_url"]
        if provider == ProviderType.OLLAMA.value:
            return f"{base_url}/api/generate"
        elif provider == ProviderType.OPENAI.value:
            return f"{base_url}/chat/completions"
        elif provider == ProviderType.ANTHROPIC.value:
            return f"{base_url}/messages"
        else:
            return base_url

    def _get_request_headers(self, model: Dict[str, Any]) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        provider = model["provider"]
        api_key = model.get("api_key")
        if provider == ProviderType.OPENAI.value and api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        elif provider == ProviderType.ANTHROPIC.value and api_key:
            headers["x-api-key"] = api_key
            headers["anthropic-version"] = "2023-06-01"
        custom_headers = model.get("headers", {})
        headers.update(custom_headers)
        return headers

    async def _make_request(self, url: str, method: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        logger.info("event=make_request url=%s method=%s", url, method)
        async with httpx.AsyncClient(timeout=float(timeout)) as client:
            if method == "POST":
                response = await client.post(url, json=payload, headers=headers)
            else:
                response = await client.get(url, headers=headers)
            if response.status_code == 200:
                logger.info("event=make_request_success url=%s", url)
                return response.json()
            logger.error("event=make_request_error url=%s status=%d body=%s", url, response.status_code, response.text[:500])
            raise Exception(f"Request failed: {response.status_code} - {response.text[:200]}")

    def _map_response(self, raw_response: Dict[str, Any], mapping: Dict[str, Any]) -> str:
        content_field = mapping.get("content_field", "response")
        if content_field in raw_response:
            return raw_response[content_field]
        if "choices" in raw_response and len(raw_response["choices"]) > 0:
            return raw_response["choices"][0].get("message", {}).get("content", "")
        if "content" in raw_response and isinstance(raw_response["content"], list):
            return raw_response["content"][0].get("text", "")
        return str(raw_response)

    def _extract_response_content(self, response: Dict[str, Any], provider: str) -> str:
        if provider == ProviderType.OLLAMA.value:
            return response.get("response", "")
        elif provider == ProviderType.OPENAI.value:
            if "choices" in response and len(response["choices"]) > 0:
                return response["choices"][0].get("message", {}).get("content", "")
        elif provider == ProviderType.ANTHROPIC.value:
            if "content" in response and isinstance(response["content"], list):
                return response["content"][0].get("text", "")
        return str(response)


request_handler = RequestHandler()
