from typing import Protocol, Any

class PagerDutyPort(Protocol):
    def trigger_incident(
        self,
        summary: str,
        severity: str,
        source: str,
        custom_details: dict[str, Any] | None = None
    ) -> str | None: ...

    def resolve_incident(
        self,
        dedup_key: str
    ) -> None: ...

