from typing import Protocol, List, Tuple

class RedisPort(Protocol):
    def scan_slo_keys(self) -> List[Tuple[str, str]]:
        """Scans Redis for slo:total keys and returns a list of unique (model, endpoint) pairs."""
        ...

    def get_slo_buckets(
        self, model: str, endpoint: str, buckets: List[int]
    ) -> Tuple[List[int], List[int]]:
        """Fetches errors and total counts for the specified buckets.
        Returns a tuple of (errors_list, total_list).
        """
        ...

    def write_burn_rate(
        self, window: str, model: str, endpoint: str, burn_rate: float, ttl: int
    ) -> None:
        """Writes the computed burn rate to slo:burn:{window}:{model}:{endpoint} with TTL."""
        ...

    def check_and_set_dedup_lock(
        self, model: str, endpoint: str, severity: str, ttl: int
    ) -> bool:
        """Attempts to set a rate limit key for deduplication.
        Returns True if the lock was acquired (meaning no alert exists/emitted recently).
        Returns False if the lock exists (dedup hit).
        """
        ...

    def write_budget_remaining(
        self, model: str, endpoint: str, budget_remaining_pct: float, ttl: int
    ) -> None:
        """Writes budget_remaining_pct to Redis."""
        ...

    def get_ddsketch_percentiles(
        self, model: str, endpoint: str, hour_of_day: int
    ) -> Tuple[float, float]:
        """Fetches P95 and P99 percentiles from DDSketch stored in Redis.
        Returns (p95, p99) falling back to (0.0, 0.0) if missing or error.
        """
        ...
