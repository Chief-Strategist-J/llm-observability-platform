import importlib.util
import functools
from typing import Any
from ...ports import PatcherPort
from .base import execute_external_call_async, execute_external_call_sync
from ....manual_instrumentation.service import llm_span
from ...domain.mappers import ProviderMapper

class LangChainPatcher(PatcherPort):
    def __init__(self):
        self._original_ainvoke = None
        self._original_invoke = None

    def is_installed(self) -> bool:
        return importlib.util.find_spec("langchain_core") is not None

    def patch(self) -> None:
        if not self.is_installed():
            return

        from langchain_core.language_models.chat_models import BaseChatModel

        # Patch Async
        self._original_ainvoke = BaseChatModel.ainvoke
        @functools.wraps(self._original_ainvoke)
        async def patched_ainvoke(instance, *args, **kwargs):
            model = getattr(instance, "model_name", getattr(instance, "model", "unknown"))
            provider = instance.__class__.__name__
            
            async with llm_span(model=model, provider=f"langchain:{provider}") as span:
                response = await execute_external_call_async(self._original_ainvoke, instance, *args, **kwargs)
                metadata = ProviderMapper.map_langchain_response(response, model, provider)
                for key, value in metadata.items():
                    span.set_metadata(key, value)
                return response
        BaseChatModel.ainvoke = patched_ainvoke

        # Patch Sync
        self._original_invoke = BaseChatModel.invoke
        @functools.wraps(self._original_invoke)
        def patched_invoke(instance, *args, **kwargs):
            model = getattr(instance, "model_name", getattr(instance, "model", "unknown"))
            provider = instance.__class__.__name__
            
            with llm_span(model=model, provider=f"langchain:{provider}") as span:
                response = execute_external_call_sync(self._original_invoke, instance, *args, **kwargs)
                metadata = ProviderMapper.map_langchain_response(response, model, provider)
                for key, value in metadata.items():
                    span.set_metadata(key, value)
                return response
        BaseChatModel.invoke = patched_invoke

    def patch_instance(self, instance: Any) -> None:
        if not self.is_installed():
            return
        import types
        import inspect
        
        for method_name in ["invoke", "ainvoke"]:
            if not hasattr(instance, method_name):
                continue
                
            original_method = getattr(instance, method_name)
            if inspect.iscoroutinefunction(original_method):
                @functools.wraps(original_method)
                async def patched_method(*args, **kwargs):
                    model = getattr(instance, "model_name", getattr(instance, "model", "unknown"))
                    provider = instance.__class__.__name__
                    async with llm_span(model=model, provider=f"langchain:{provider}") as span:
                        response = await execute_external_call_async(original_method, *args, **kwargs)
                        metadata = ProviderMapper.map_langchain_response(response, model, provider)
                        for key, value in metadata.items():
                            span.set_metadata(key, value)
                        return response
            else:
                @functools.wraps(original_method)
                def patched_method(*args, **kwargs):
                    model = getattr(instance, "model_name", getattr(instance, "model", "unknown"))
                    provider = instance.__class__.__name__
                    with llm_span(model=model, provider=f"langchain:{provider}") as span:
                        response = execute_external_call_sync(original_method, *args, **kwargs)
                        metadata = ProviderMapper.map_langchain_response(response, model, provider)
                        for key, value in metadata.items():
                            span.set_metadata(key, value)
                        return response
            
            setattr(instance, method_name, types.MethodType(patched_method, instance))

    def unpatch(self) -> None:
        from langchain_core.language_models.chat_models import BaseChatModel
        if self._original_ainvoke:
            BaseChatModel.ainvoke = self._original_ainvoke
            self._original_ainvoke = None
        if self._original_invoke:
            BaseChatModel.invoke = self._original_invoke
            self._original_invoke = None
