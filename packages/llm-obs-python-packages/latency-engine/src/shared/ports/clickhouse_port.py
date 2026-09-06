from typing import Protocol

class ClickHousePort(Protocol):
    def insert_latency_checkpoints(self, rows: list[tuple]) -> None:
        """Inserts hourly latency checkpoints into ClickHouse."""
        ...

    def get_p99_ttft_history_7d(self, model: str, endpoint: str, hour_of_day: int) -> list[float]:
        """Queries p99_ttft_ms for the same model, endpoint, and hour_of_day over the last 7 days."""
        ...
