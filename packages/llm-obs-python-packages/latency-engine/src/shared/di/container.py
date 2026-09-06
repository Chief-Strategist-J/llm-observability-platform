from __future__ import annotations

from typing import Any


class ServiceContainer:
    _registry: dict[str, Any] = {}

    @classmethod
    def register(cls, name: str, instance: Any) -> None:
        cls._registry[name] = instance

    @classmethod
    def resolve(cls, name: str) -> Any:
        if name not in cls._registry:
            raise KeyError(f"Service {name} not found in container")
        return cls._registry[name]
