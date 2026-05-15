import importlib.util
import functools
from typing import Any
from ...ports import PatcherPort
from .base import execute_external_call_async, execute_external_call_sync
from ...domain.mappers import ProviderMapper
from ....manual_instrumentation.service import llm_span

class LiteLLMPatcher(PatcherPort):
    def __init__(self):
        self._original_acompletion = None
        self._original_completion = None

    def is_installed(self) -> bool:
        return importlib.util.find_spec("litellm") is not None

    def patch(self) -> None:
        if not self.is_installed():
            return

        import litellm
        
        # Patch Async
        self._original_acompletion = litellm.acompletion
        @functools.wraps(self._original_acompletion)
        async def patched_acompletion(*args, **kwargs):
            model = kwargs.get("model", "unknown")
            async with llm_span(model=model, provider="litellm") as span:
                response = await execute_external_call_async(self._original_acompletion, *args, **kwargs)
                metadata = ProviderMapper.map_openai_response(response)
                metadata["provider"] = "litellm"
                for key, value in metadata.items():
                    span.set_metadata(key, value)
                return response
        litellm.acompletion = patched_acompletion

        # Patch Sync
        self._original_completion = litellm.completion
        @functools.wraps(self._original_completion)
        def patched_completion(*args, **kwargs):
            model = kwargs.get("model", "unknown")
            with llm_span(model=model, provider="litellm") as span:
                response = execute_external_call_sync(self._original_completion, *args, **kwargs)
                metadata = ProviderMapper.map_openai_response(response)
                metadata["provider"] = "litellm"
                for key, value in metadata.items():
                    span.set_metadata(key, value)
                return response
        litellm.completion = patched_completion

    def patch_instance(self, instance: Any) -> None:
        import types
        import inspect
        for attr in ["completion", "acompletion"]:
            if hasattr(instance, attr):
                original = getattr(instance, attr)
                if inspect.iscoroutinefunction(original):
                    @functools.wraps(original)
                    async def patched(*args, **kwargs):
                        model = kwargs.get("model", "unknown")
                        async with llm_span(model=model, provider="litellm") as span:
                            response = await execute_external_call_async(original, *args, **kwargs)
                            metadata = ProviderMapper.map_openai_response(response)
                            metadata["provider"] = "litellm"
                            for key, value in metadata.items():
                                span.set_metadata(key, value)
                            return response
                else:
                    @functools.wraps(original)
                    def patched(*args, **kwargs):
                        model = kwargs.get("model", "unknown")
                        with llm_span(model=model, provider="litellm") as span:
                            response = execute_external_call_sync(original, *args, **kwargs)
                            metadata = ProviderMapper.map_openai_response(response)
                            metadata["provider"] = "litellm"
                            for key, value in metadata.items():
                                span.set_metadata(key, value)
                            return response
                setattr(instance, attr, types.MethodType(patched, instance))

    def unpatch(self) -> None:
        import litellm
        if self._original_acompletion:
            litellm.acompletion = self._original_acompletion
            self._original_acompletion = None
        if self._original_completion:
            litellm.completion = self._original_completion
            self._original_completion = None
