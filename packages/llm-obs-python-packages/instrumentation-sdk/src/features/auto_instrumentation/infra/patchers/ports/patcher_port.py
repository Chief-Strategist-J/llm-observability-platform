from typing import Protocol, Any

class PatcherPort(Protocol):
    def is_installed(self) -> bool:
        ...

    def patch(self) -> None:
        ...

    def patch_instance(self, instance: Any) -> None:
        ...

    def unpatch(self) -> None:
        ...
