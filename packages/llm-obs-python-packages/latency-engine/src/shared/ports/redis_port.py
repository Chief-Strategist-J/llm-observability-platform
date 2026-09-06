from typing import Protocol

class RedisPort(Protocol):
    def scan_keys(self, pattern: str) -> list[str]:
        """Scans keys in Redis matching the pattern."""
        ...

    def get_key(self, key: str) -> str | None:
        """Gets value of a key from Redis."""
        ...

    def get_slo_violation_count(self, model: str, endpoint: str, hour_timestamp: int) -> int:
        """Sums up the SLO error counters for a given hour."""
        ...

    def set_baseline_p99_ttft(self, model: str, endpoint: str, hour_of_day: int, value: float) -> None:
        """Sets the baseline p99 ttft in Redis."""
        ...
