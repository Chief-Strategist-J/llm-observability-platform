import importlib.util
import functools
from typing import Any
from ...ports import PatcherPort
from .base import execute_external_call_async, execute_external_call_sync
from ...domain.mappers import ProviderMapper
from ....manual_instrumentation.service import llm_span

class AnthropicPatcher(PatcherPort):
    def __init__(self):
        self._original_async_create = None
        self._original_sync_create = None

    def is_installed(self) -> bool:
        return importlib.util.find_spec("anthropic") is not None

    def patch(self) -> None:
        if not self.is_installed():
            return

        from anthropic.resources.messages import AsyncMessages, Messages

        # Patch Async
        self._original_async_create = AsyncMessages.create
        @functools.wraps(self._original_async_create)
        async def patched_async_create(instance, *args, **kwargs):
            model = kwargs.get("model", "unknown")
            async with llm_span(model=model, provider="anthropic") as span:
                response = await execute_external_call_async(self._original_async_create, instance, *args, **kwargs)
                metadata = ProviderMapper.map_anthropic_response(response)
                for key, value in metadata.items():
                    span.set_metadata(key, value)
                return response
        AsyncMessages.create = patched_async_create

        # Patch Sync
        self._original_sync_create = Messages.create
        @functools.wraps(self._original_sync_create)
        def patched_sync_create(instance, *args, **kwargs):
            model = kwargs.get("model", "unknown")
            with llm_span(model=model, provider="anthropic") as span:
                response = execute_external_call_sync(self._original_sync_create, instance, *args, **kwargs)
                metadata = ProviderMapper.map_anthropic_response(response)
                for key, value in metadata.items():
                    span.set_metadata(key, value)
                return response
        Messages.create = patched_sync_create

    def patch_instance(self, instance: Any) -> None:
        if not self.is_installed():
            return
        import types
        import inspect
        original_create = instance.messages.create
        
        if inspect.iscoroutinefunction(original_create):
            @functools.wraps(original_create)
            async def patched_create(*args, **kwargs):
                model = kwargs.get("model", "unknown")
                async with llm_span(model=model, provider="anthropic") as span:
                    response = await execute_external_call_async(original_create, *args, **kwargs)
                    metadata = ProviderMapper.map_anthropic_response(response)
                    for key, value in metadata.items():
                        span.set_metadata(key, value)
                    return response
        else:
            @functools.wraps(original_create)
            def patched_create(*args, **kwargs):
                model = kwargs.get("model", "unknown")
                with llm_span(model=model, provider="anthropic") as span:
                    response = execute_external_call_sync(original_create, *args, **kwargs)
                    metadata = ProviderMapper.map_anthropic_response(response)
                    for key, value in metadata.items():
                        span.set_metadata(key, value)
                    return response
                    
        instance.messages.create = types.MethodType(patched_create, instance.messages)

    def unpatch(self) -> None:
        from anthropic.resources.messages import AsyncMessages, Messages
        if self._original_async_create:
            AsyncMessages.create = self._original_async_create
            self._original_async_create = None
        if self._original_sync_create:
            Messages.create = self._original_sync_create
            self._original_sync_create = None
