from typing import List, Dict, Any, Type
from .ports import PatcherPort

class AutoInstrumentationService:
    def __init__(self, patchers: List[PatcherPort]):
        self._patchers = patchers
        self._active_patchers: List[PatcherPort] = []
        self._is_instrumented = False

    def instrument_all(self) -> None:
        if self._is_instrumented:
            return
            
        for patcher in self._patchers:
            if patcher.is_installed():
                patcher.patch()
                self._active_patchers.append(patcher)
        self._is_instrumented = True

    def uninstrument_all(self) -> None:
        if not self._is_instrumented:
            return
            
        for patcher in self._active_patchers:
            patcher.unpatch()
        self._active_patchers = []
        self._is_instrumented = False

    def instrument_client(self, client: Any, provider: str) -> None:
        """Manual mode for custom client instances."""
        for patcher in self._patchers:
            if provider.lower() in patcher.__class__.__name__.lower() and patcher.is_installed():
                patcher.patch_instance(client)
                return
