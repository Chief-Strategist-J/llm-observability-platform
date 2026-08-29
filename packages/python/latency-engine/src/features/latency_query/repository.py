from __future__ import annotations
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.ports.latency_redis_port import LatencyRedisPort
    from shared.ports.latency_clickhouse_port import LatencyClickHousePort, BaselineRow

logger = logging.getLogger(__name__)

class LatencyQueryRepository:
    def __init__(self, redis: LatencyRedisPort, clickhouse: LatencyClickHousePort) -> None:
        self._redis = redis
        self._clickhouse = clickhouse

    def get_sketch_b64(self, model: str, hour_of_day: int) -> str | None:
        try:
            return self._redis.get_sketch_b64(model, hour_of_day)
        except Exception as exc:
            logger.debug("Redis query failed for sketch_b64: %s", exc)
            return None

    def get_slo_counts(
        self,
        model: str,
        endpoint: str,
        window_minutes: int,
    ) -> tuple[int, int]:
        try:
            return self._redis.get_slo_counts(model, endpoint, window_minutes)
        except Exception as exc:
            logger.debug("Redis query failed for slo_counts: %s", exc)
            return 0, 0

    def get_baseline(
        self,
        model: str,
        hour_of_day: int,
        days: int,
    ) -> list[BaselineRow]:
        try:
            return self._clickhouse.get_baseline(model, hour_of_day, days)
        except Exception as exc:
            logger.debug("ClickHouse query failed for baseline: %s", exc)
            return []

    def get_attribution(self, model: str, hour: str) -> dict[str, float] | None:
        try:
            return self._redis.get_attribution_avg(model, hour)
        except Exception as exc:
            logger.debug("Redis query failed for attribution: %s", exc)
            return None
