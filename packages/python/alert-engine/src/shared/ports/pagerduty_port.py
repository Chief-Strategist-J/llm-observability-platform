from typing import Protocol, Any

class PagerDutyPort(Protocol):
    def trigger_incident(
        self,
        summary: str,
        severity: str,
        source: str,
        custom_details: dict[str, Any] | None = None
    ) -> None: ...
