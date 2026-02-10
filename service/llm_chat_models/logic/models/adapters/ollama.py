import time
import enum
import httpx
import json
from typing import AsyncGenerator, Dict, Any, Optional
from config.settings import OLLAMA_HOST, CIRCUIT_BREAKER_FAILURE_THRESHOLD, CIRCUIT_BREAKER_RECOVERY_TIMEOUT
from telemetry.logger import log_event, get_tracer, trace_with_details
from .base import BaseModelAdapter

class CircuitState(enum.Enum):
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'

class CircuitBreaker:

    def __init__(self, failure_threshold: int=CIRCUIT_BREAKER_FAILURE_THRESHOLD, recovery_timeout: float=CIRCUIT_BREAKER_RECOVERY_TIMEOUT):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.success_count = 0

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                log_event('circuit_breaker_half_open')
                return True
            return False
        return True

    def record_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            log_event('circuit_breaker_closed')
        self.success_count += 1

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            log_event('circuit_breaker_reopened', failures=self.failure_count)
            return
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            log_event('circuit_breaker_opened', failures=self.failure_count, threshold=self.failure_threshold)

class OllamaAdapter(BaseModelAdapter):

    def __init__(self):
        self.base_url = OLLAMA_HOST
        self._breaker = CircuitBreaker()
        log_event('ollama_adapter_init', host=self.base_url)

    def _check_circuit(self):
        if not self._breaker.can_execute():
            raise ConnectionError(f'Circuit breaker OPEN: Ollama at {self.base_url} is unavailable. Retry after {self._breaker.recovery_timeout}s.')

    @trace_with_details(get_tracer())
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict]=None) -> httpx.Response:
        self._check_circuit()
        url = f'{self.base_url}{endpoint}'
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                if method == 'GET':
                    response = await client.get(url)
                elif method == 'POST':
                    response = await client.post(url, json=data)
                elif method == 'DELETE':
                    response = await client.delete(url, json=data)
                else:
                    raise ValueError(f'Unsupported method: {method}')
                self._breaker.record_success()
                return response
        except (httpx.ConnectError, httpx.TimeoutException, OSError) as e:
            self._breaker.record_failure()
            raise

    @trace_with_details(get_tracer())
    async def download_model(self, model_name: str) -> bool:
        self._check_circuit()
        log_event('model_download_start', model=model_name)
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream('POST', f'{self.base_url}/api/pull', json={'name': model_name}) as response:
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            if 'error' in data:
                                log_event('model_download_error', model=model_name, error=data['error'])
                                return False
                            if data.get('status') == 'success':
                                log_event('model_download_success', model=model_name)
                                self._breaker.record_success()
                                return True
            self._breaker.record_success()
            return True
        except (httpx.ConnectError, httpx.TimeoutException, OSError) as e:
            self._breaker.record_failure()
            log_event('model_download_exception', model=model_name, error=str(e))
            raise

    @trace_with_details(get_tracer())
    async def delete_model(self, model_name: str) -> bool:
        log_event('model_delete_start', model=model_name)
        response = await self._make_request('DELETE', '/api/delete', {'name': model_name})
        if response.status_code == 200:
            log_event('model_delete_success', model=model_name)
            return True
        log_event('model_delete_failed', model=model_name, status=response.status_code)
        return False

    @trace_with_details(get_tracer())
    async def list_models(self) -> list:
        response = await self._make_request('GET', '/api/tags')
        if response.status_code == 200:
            models = response.json().get('models', [])
            return [m['name'].split(':')[0] for m in models]
        return []

    @trace_with_details(get_tracer())
    async def get_model_status(self, model_name: str) -> Dict[str, Any]:
        current_models = await self.list_models()
        is_downloaded = model_name in current_models or f'{model_name}:latest' in current_models
        return {'name': model_name, 'status': 'available' if is_downloaded else 'not_found', 'backend': 'ollama'}

    @trace_with_details(get_tracer())
    async def generate_response(self, model_name: str, prompt: str, **kwargs) -> Dict[str, Any]:
        log_event('generate_response_start', model=model_name)
        payload = {'model': model_name, 'prompt': prompt, 'stream': False, **kwargs}
        response = await self._make_request('POST', '/api/generate', payload)
        if response.status_code == 200:
            result = response.json()
            log_event('generate_response_success', model=model_name)
            return {'response': result.get('response'), 'done': True, 'context': result.get('context')}
        log_event('generate_response_failed', model=model_name, status=response.status_code)
        return {'error': f'Ollama API Error: {response.status_code}'}

    @trace_with_details(get_tracer())
    async def generate_stream(self, model_name: str, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        self._check_circuit()
        log_event('generate_stream_start', model=model_name)
        payload = {'model': model_name, 'prompt': prompt, 'stream': True, **kwargs}
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream('POST', f'{self.base_url}/api/generate', json=payload) as response:
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            if 'response' in data:
                                yield data['response']
                            if data.get('done'):
                                self._breaker.record_success()
                                log_event('generate_stream_complete', model=model_name)
        except (httpx.ConnectError, httpx.TimeoutException, OSError) as e:
            self._breaker.record_failure()
            raise