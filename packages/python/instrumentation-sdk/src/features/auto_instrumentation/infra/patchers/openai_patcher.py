import importlib.util
import functools
import time
from typing import Any, Optional
from ...ports import PatcherPort
from .base import execute_external_call_async, execute_external_call_sync
from ...domain.mappers import ProviderMapper
from ....manual_instrumentation.service import llm_span

class OpenAIPatcher(PatcherPort):
    def __init__(self):
        self._original_async_create = None
        self._original_sync_create = None

    def is_installed(self) -> bool:
        return importlib.util.find_spec("openai") is not None

    def patch(self) -> None:
        if not self.is_installed():
            return

        import openai
        from openai.resources.chat.completions import AsyncCompletions, Completions

        # Patch Async
        self._original_async_create = AsyncCompletions.create
        @functools.wraps(self._original_async_create)
        async def patched_async_create(instance, *args, **kwargs):
            model = kwargs.get("model", "unknown")
            async with llm_span(model=model, provider="openai") as span:
                response = await execute_external_call_async(self._original_async_create, instance, *args, **kwargs)
                metadata = ProviderMapper.map_openai_response(response)
                for key, value in metadata.items():
                    span.set_metadata(key, value)
                return response
        AsyncCompletions.create = patched_async_create

        # Patch Sync
        self._original_sync_create = Completions.create
        @functools.wraps(self._original_sync_create)
        def patched_sync_create(instance, *args, **kwargs):
            model = kwargs.get("model", "unknown")
            with llm_span(model=model, provider="openai") as span:
                response = execute_external_call_sync(self._original_sync_create, instance, *args, **kwargs)
                metadata = ProviderMapper.map_openai_response(response)
                for key, value in metadata.items():
                    span.set_metadata(key, value)
                return response
        Completions.create = patched_sync_create

    def patch_instance(self, instance: Any) -> None:
        if not self.is_installed():
            return
            
        import types
        import inspect
        original_create = instance.chat.completions.create
        
        if inspect.iscoroutinefunction(original_create):
            @functools.wraps(original_create)
            async def patched_create(*args, **kwargs):
                model = kwargs.get("model", "unknown")
                async with llm_span(model=model, provider="openai") as span:
                    response = await execute_external_call_async(original_create, *args, **kwargs)
                    metadata = ProviderMapper.map_openai_response(response)
                    for key, value in metadata.items():
                        span.set_metadata(key, value)
                    return response
        else:
            @functools.wraps(original_create)
            def patched_create(*args, **kwargs):
                model = kwargs.get("model", "unknown")
                with llm_span(model=model, provider="openai") as span:
                    response = execute_external_call_sync(original_create, *args, **kwargs)
                    metadata = ProviderMapper.map_openai_response(response)
                    for key, value in metadata.items():
                        span.set_metadata(key, value)
                    return response

        instance.chat.completions.create = types.MethodType(patched_create, instance.chat.completions)

    def unpatch(self) -> None:
        from openai.resources.chat.completions import AsyncCompletions, Completions
        if self._original_async_create:
            AsyncCompletions.create = self._original_async_create
            self._original_async_create = None
        if self._original_sync_create:
            Completions.create = self._original_sync_create
            self._original_sync_create = None
