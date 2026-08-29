"""
Algorithm Summary: Data Access Repository for Latency Queries.
Provides centralized data retrieval methods for Redis sketch structures, SLO error budget counts,
ClickHouse historical percentile baselines, and request duration attributions. Encapsulates all backend
storage interactions and uses centralized repository error handling decorators to catch infrastructure errors
and return fallback zero-state payloads without leaking infrastructure exceptions into domain logic.
"""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from shared.errors.repository_error_handler import handle_repository_errors

if TYPE_CHECKING:
    from shared.ports.latency_redis_port import LatencyRedisPort
    from shared.ports.latency_clickhouse_port import LatencyClickHousePort, BaselineRow

logger = logging.getLogger(__name__)

class LatencyQueryRepository:
    def __init__(self, redis: LatencyRedisPort, clickhouse: LatencyClickHousePort) -> None:
        self._redis = redis
        self._clickhouse = clickhouse

    @handle_repository_errors(default_factory=None)
    def get_sketch_b64(self, model: str, hour_of_day: int) -> str | None:
        return self._redis.get_sketch_b64(model, hour_of_day)

    @handle_repository_errors(default_factory=lambda: (0, 0))
    def get_slo_counts(
        self,
        model: str,
        endpoint: str,
        window_minutes: int,
    ) -> tuple[int, int]:
        return self._redis.get_slo_counts(model, endpoint, window_minutes)

    @handle_repository_errors(default_factory=list)
    def get_baseline(
        self,
        model: str,
        hour_of_day: int,
        days: int,
    ) -> list[BaselineRow]:
        return self._clickhouse.get_baseline(model, hour_of_day, days)

    @handle_repository_errors(default_factory=None)
    def get_attribution(self, model: str, hour: str) -> dict[str, float] | None:
        return self._redis.get_attribution_avg(model, hour)
