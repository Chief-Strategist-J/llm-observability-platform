from typing import Protocol

class ClickHousePort(Protocol):
    def get_baseline_p95_7d(self, model: str, endpoint: str) -> float:
        """Fetches 7-day baseline P95 from ClickHouse.
        First attempts from latency_checkpoints, then falls back to calculating
        from raw llm_spans if latency_checkpoints table is missing or empty.
        """
        ...
