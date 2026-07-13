from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.ports.latency_redis_port import LatencyRedisPort
    from shared.ports.latency_clickhouse_port import LatencyClickHousePort, BaselineRow


class LatencyQueryRepository:
    """
    Decoupled repository for all database queries in the latency layer.
    """

    def __init__(self, redis: LatencyRedisPort, clickhouse: LatencyClickHousePort) -> None:
        self._redis = redis
        self._clickhouse = clickhouse

    def get_sketch_b64(self, model: str, hour_of_day: int) -> str | None:
        return self._redis.get_sketch_b64(model, hour_of_day)

    def get_slo_counts(
        self,
        model: str,
        endpoint: str,
        window_minutes: int,
    ) -> tuple[int, int]:
        return self._redis.get_slo_counts(model, endpoint, window_minutes)

    def get_baseline(
        self,
        model: str,
        hour_of_day: int,
        days: int,
    ) -> list[BaselineRow]:
        return self._clickhouse.get_baseline(model, hour_of_day, days)

    def get_attribution(self, model: str, hour: str) -> dict[str, float] | None:
        return self._redis.get_attribution_avg(model, hour)
