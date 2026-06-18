import logging
import os
import yaml
from datetime import datetime, timezone
from typing import List, Tuple, Dict
from temporalio import activity
from shared.ports.redis_port import RedisPort
from shared.ports.clickhouse_port import ClickHousePort
from shared.ports.kafka_port import KafkaPort
from shared.ports.metrics_port import MetricsPort
from features.slo.service import SloService
from shared.tracing.tracer import trace_span

logger = logging.getLogger(__name__)

class SloBurnActivities:
    def __init__(
        self,
        redis: RedisPort,
        clickhouse: ClickHousePort,
        kafka: KafkaPort,
        metrics: MetricsPort,
        slo_compliance_config_path: str,
        default_slo_compliance: float,
    ):
        self.redis = redis
        self.clickhouse = clickhouse
        self.kafka = kafka
        self.metrics = metrics
        self.slo_compliance_config_path = slo_compliance_config_path
        self.default_slo_compliance = default_slo_compliance
        self._load_slo_compliance_config()

    def _load_slo_compliance_config(self) -> None:
        self.compliance_map = {}
        try:
            if os.path.exists(self.slo_compliance_config_path):
                with open(self.slo_compliance_config_path, "r") as f:
                    cfg = yaml.safe_load(f) or {}
                    self.compliance_map = cfg.get("compliance", {})
        except Exception as e:
            logger.warning("Failed to load compliance config: %s", e)

    def _get_slo_compliance(self, endpoint: str) -> float:
        val = self.compliance_map.get(endpoint)
        if val is None:
            val = self.compliance_map.get("default")
        if val is None:
            val = self.default_slo_compliance
        return float(val)

    @activity.defn(name="fetch_active_pairs")
    async def fetch_active_pairs(self) -> List[Tuple[str, str]]:
        info = activity.info()
        with trace_span(
            "fetch_active_pairs",
            attributes={
                "activity.type": "fetch_active_pairs",
                "workflow.id": info.workflow_id,
                "workflow.run_id": info.workflow_run_id,
            },
        ):
            return self.redis.scan_slo_keys()

    @activity.defn(name="compute_burn_rates")
    async def compute_burn_rates(self, model: str, endpoint: str, unix_ts: int) -> Dict[str, float]:
        info = activity.info()
        with trace_span(
            "compute_burn_rates",
            attributes={
                "activity.type": "compute_burn_rates",
                "workflow.id": info.workflow_id,
                "workflow.run_id": info.workflow_run_id,
                "model": model,
                "endpoint": endpoint,
            },
        ):
            now_bucket = unix_ts // 60
            slo_threshold = self._get_slo_compliance(endpoint)

            # Fast: 5 min
            fast_buckets = SloService.get_window_buckets(now_bucket, 5)
            fast_errors, fast_totals = self.redis.get_slo_buckets(model, endpoint, fast_buckets)
            burn_fast = SloService.compute_burn_rate(sum(fast_errors), sum(fast_totals), slo_threshold)

            # Medium: 1 hr
            medium_buckets = SloService.get_window_buckets(now_bucket, 60)
            med_errors, med_totals = self.redis.get_slo_buckets(model, endpoint, medium_buckets)
            burn_med = SloService.compute_burn_rate(sum(med_errors), sum(med_totals), slo_threshold)

            # Slow: 6 hr
            slow_buckets = SloService.get_window_buckets(now_bucket, 360)
            slow_errors, slow_totals = self.redis.get_slo_buckets(model, endpoint, slow_buckets)
            burn_slow = SloService.compute_burn_rate(sum(slow_errors), sum(slow_totals), slo_threshold)

            self.metrics.record_burn_rate_computed(model, endpoint)

            return {
                "fast": burn_fast,
                "medium": burn_med,
                "slow": burn_slow,
            }

    @activity.defn(name="write_burn_rates")
    async def write_burn_rates(self, model: str, endpoint: str, burn_rates_dict: Dict[str, float]) -> None:
        info = activity.info()
        with trace_span(
            "write_burn_rates",
            attributes={
                "activity.type": "write_burn_rates",
                "workflow.id": info.workflow_id,
                "workflow.run_id": info.workflow_run_id,
                "model": model,
                "endpoint": endpoint,
            },
        ):
            self.redis.write_burn_rate("fast", model, endpoint, burn_rates_dict["fast"], 300)
            self.redis.write_burn_rate("medium", model, endpoint, burn_rates_dict["medium"], 7200)
            self.redis.write_burn_rate("slow", model, endpoint, burn_rates_dict["slow"], 86400)

    @activity.defn(name="handle_alerts")
    async def handle_alerts(self, model: str, endpoint: str, burn_rates_dict: Dict[str, float], unix_ts: int) -> None:
        info = activity.info()
        with trace_span(
            "handle_alerts",
            attributes={
                "activity.type": "handle_alerts",
                "workflow.id": info.workflow_id,
                "workflow.run_id": info.workflow_run_id,
                "model": model,
                "endpoint": endpoint,
            },
        ):
            fast = burn_rates_dict["fast"]
            medium = burn_rates_dict["medium"]
            slow = burn_rates_dict["slow"]

            severity = SloService.determine_severity(fast, medium, slow)
            if severity is None:
                return

            # F-L-09 Dedup Rate Limit TTLs
            dedup_ttls = {
                "page": 900,
                "slack": 3600,
                "ticket": 86400
            }
            ttl = dedup_ttls.get(severity, 900)

            # Try to acquire rate-limit lock in Redis
            acquired = self.redis.check_and_set_dedup_lock(model, endpoint, severity, ttl)
            if not acquired:
                logger.info("Alert suppressed for model=%s endpoint=%s severity=%s (dedup hit)", model, endpoint, severity)
                self.metrics.record_alert_deduped(model, endpoint, severity)
                return

            # Fetch percentiles from DDSketch for current hour of day
            dt = datetime.fromtimestamp(unix_ts, tz=timezone.utc)
            hour_of_day = dt.hour
            p95, p99 = self.redis.get_ddsketch_percentiles(model, endpoint, hour_of_day)

            # Fetch 7-day baseline P95 from ClickHouse
            baseline_p95 = self.clickhouse.get_baseline_p95_7d(model, endpoint)

            # Compute budget remaining pct from 30-day (43,200 minutes) error count
            now_bucket = unix_ts // 60
            # MGET 43,200 buckets in batches of 5,000 to prevent Redis block
            all_errors_30d = 0
            all_totals_30d = 0
            batch_size = 5000
            total_buckets = 43200
            
            for start_idx in range(0, total_buckets, batch_size):
                size = min(batch_size, total_buckets - start_idx)
                buckets = [now_bucket - total_buckets + start_idx + i for i in range(size)]
                batch_errors, batch_totals = self.redis.get_slo_buckets(model, endpoint, buckets)
                all_errors_30d += sum(batch_errors)
                all_totals_30d += sum(batch_totals)

            slo_threshold = self._get_slo_compliance(endpoint)
            budget_remaining_pct = SloService.compute_budget_remaining_pct(
                all_errors_30d, all_totals_30d, slo_threshold
            )

            # Write budget remaining to Redis
            self.redis.write_budget_remaining(model, endpoint, budget_remaining_pct, 86400)

            # Publish to Kafka alerts.latency.slo topic
            alert_payload = {
                "model": model,
                "endpoint": endpoint,
                "severity": severity,
                "burn_rate_fast": fast,
                "burn_rate_medium": medium,
                "burn_rate_slow": slow,
                "p95": p95,
                "p99": p99,
                "baseline_p95": baseline_p95,
                "budget_remaining_pct": budget_remaining_pct,
                "timestamp": dt.isoformat(),
            }

            self.kafka.publish_alert(
                topic="alerts.latency.slo",
                key=f"{model}:{endpoint}",
                payload=alert_payload
            )

            self.metrics.record_alert_sent(model, endpoint, severity)
