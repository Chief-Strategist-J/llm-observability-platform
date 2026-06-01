from __future__ import annotations

from typing import Protocol

class AlertPublisherPort(Protocol):
    def publish_alert(self, message: str, metadata: dict[str, str] | None = None) -> None: ...
