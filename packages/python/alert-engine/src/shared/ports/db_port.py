from typing import Protocol, Any

class DbPort(Protocol):
    def insert_alert(
        self,
        alert_type: str,
        service: str | None,
        model: str | None,
        user_id: str | None,
        event_type: str | None,
        payload: dict[str, Any],
        delivery_latency_ms: int | None
    ) -> None: ...
