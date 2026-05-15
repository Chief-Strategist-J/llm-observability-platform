from typing import Any, Protocol, runtime_checkable

@runtime_checkable
class PatcherPort(Protocol):
    def patch(self) -> None:
        ...

    def unpatch(self) -> None:
        ...

    def patch_instance(self, instance: Any) -> None:
        ...

    def is_installed(self) -> bool:
        ...
