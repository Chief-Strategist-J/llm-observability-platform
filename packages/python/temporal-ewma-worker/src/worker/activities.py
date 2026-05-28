import os
import yaml
from typing import List, Tuple
from temporalio import activity
from shared.ports.clickhouse_port import ClickHousePort
from shared.ports.redis_port import RedisPort
from shared.ports.postgres_port import PostgresPort
from shared.ports.alert_publisher_port import AlertPublisherPort
from shared.ports.metrics_port import MetricsPort
from shared.types.ewma_types import EwmaRecord, ClusterCost, AnomalyPayload


class EwmaActivities:
    def __init__(
        self,
        clickhouse: ClickHousePort,
        redis: RedisPort,
        postgres: PostgresPort,
        alert_publisher: AlertPublisherPort,
        metrics: MetricsPort,
    ):
        self.clickhouse = clickhouse
        self.redis = redis
        self.postgres = postgres
        self.alert_publisher = alert_publisher
        self.metrics = metrics

    @activity.defn(name="fetch_active_pairs")
    async def fetch_active_pairs(self) -> List[Tuple[str, str]]:
        return self.clickhouse.get_active_pairs()

    @activity.defn(name="fetch_cost_history")
    async def fetch_cost_history(
        self, service: str, model: str, hour_of_week: int
    ) -> List[float]:
        return self.clickhouse.get_cost_history(service, model, hour_of_week)

    @activity.defn(name="fetch_global_model_avg")
    async def fetch_global_model_avg(self, model: str, hour_of_week: int) -> float:
        return self.clickhouse.get_global_model_avg(model, hour_of_week)

    @activity.defn(name="fetch_current_cost_1h")
    async def fetch_current_cost_1h(self, service: str, model: str) -> float:
        return self.clickhouse.get_current_cost_1h(service, model)

    @activity.defn(name="fetch_cost_by_cluster_1h")
    async def fetch_cost_by_cluster_1h(
        self, service: str, model: str
    ) -> List[ClusterCost]:
        return self.clickhouse.get_cost_by_cluster_1h(service, model)

    @activity.defn(name="get_baseline")
    async def get_baseline(
        self, service: str, model: str, hour_of_week: int
    ) -> EwmaRecord | None:
        return self.postgres.get_baseline(service, model, hour_of_week)

    @activity.defn(name="upsert_baseline")
    async def upsert_baseline(self, record: EwmaRecord) -> None:
        self.postgres.upsert_baseline(record)
        self.redis.set_ewma(
            record.service, record.model, record.hour_of_week, record.ewma_value
        )

    @activity.defn(name="publish_anomaly_alert")
    async def publish_anomaly_alert(self, payload: AnomalyPayload) -> None:
        self.alert_publisher.publish_anomaly(payload)

    @activity.defn(name="fetch_active_keys")
    async def fetch_active_keys(self, dimension: str) -> List[str]:
        return self.clickhouse.get_active_keys(dimension)

    @activity.defn(name="verify_key_integrity")
    async def verify_key_integrity(self, dimension: str, key: str) -> dict:
        redis_sum = self.redis.get_fenwick_sum(dimension, "1h", key)
        clickhouse_sum = self.clickhouse.get_clickhouse_sum_1h(dimension, key)

        delta = abs(clickhouse_sum - redis_sum)
        max_val = max(clickhouse_sum, redis_sum)
        is_mismatch = False

        if max_val > 0:
            ratio = delta / max_val
            if ratio > 0.01:
                is_mismatch = True
                self.metrics.record_integrity_mismatch(dimension)
                self.alert_publisher.publish_integrity_mismatch(
                    dimension, key, redis_sum, clickhouse_sum
                )

        return {
            "dimension": dimension,
            "key": key,
            "redis_sum": redis_sum,
            "clickhouse_sum": clickhouse_sum,
            "is_mismatch": is_mismatch,
        }

    @activity.defn(name="fetch_spans_for_correction")
    async def fetch_spans_for_correction(self, hours: int = 24) -> List[dict]:
        return self.clickhouse.get_spans_for_correction(hours)

    @activity.defn(name="apply_price_corrections")
    async def apply_price_corrections(self, spans: List[dict]) -> int:
        paths = [
            os.environ.get("PRICE_CONFIG_PATH", ""),
            "model_price_versions.yaml",
            "/home/btpl-lap-07/prod/llm-observability-platform/packages/python/event-cost-worker/model_price_versions.yaml",
        ]
        prices_list = []
        for p in paths:
            if p and os.path.exists(p):
                with open(p, "r") as f:
                    try:
                        cfg = yaml.safe_load(f)
                        prices_list = cfg.get("prices", [])
                        break
                    except Exception:
                        pass

        prices_map = {}
        for pr in prices_list:
            prices_map[(pr.get("model"), pr.get("provider"))] = pr

        corrections = []
        correction_count = 0
        model_corrections_count = {}

        for span in spans:
            model = span.get("model")
            provider = span.get("provider")
            price_info = prices_map.get((model, provider))
            if not price_info:
                continue

            input_price = price_info.get("input_price_per_token_micro", 0)
            output_price = price_info.get("output_price_per_token_micro", 0)
            price_ver = price_info.get("version", "")

            prompt_tokens = span.get("prompt_tokens", 0)
            completion_tokens = span.get("completion_tokens", 0)
            recorded_cost = span.get("cost_usd_micro", 0)

            expected_cost = (prompt_tokens * input_price) + (
                completion_tokens * output_price
            )
            if expected_cost != recorded_cost:
                delta = expected_cost - recorded_cost
                correction_span = dict(span)
                correction_span["span_id"] = f"correction-{span['span_id']}"
                correction_span["cost_usd_micro"] = delta
                correction_span["price_version"] = price_ver
                correction_span["prompt_tokens"] = 0
                correction_span["completion_tokens"] = 0
                corrections.append(correction_span)

                correction_count += 1
                model_corrections_count[model] = (
                    model_corrections_count.get(model, 0) + 1
                )

        if corrections:
            self.clickhouse.insert_correction_rows(corrections)
            for model, cnt in model_corrections_count.items():
                self.metrics.record_retroactive_correction(model, cnt)

        return correction_count

