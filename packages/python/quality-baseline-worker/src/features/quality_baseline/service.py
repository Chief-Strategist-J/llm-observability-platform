from typing import List, Tuple
from datetime import datetime, timezone, timedelta, time, date
from features.quality_baseline.types import BaselineRecomputeResult, DailyRollupRecord
from shared.ports.postgres_port import PostgresPort
from shared.ports.redis_port import RedisPort
from shared.ports.clickhouse_port import ClickHousePort
from shared.ports.metrics_port import MetricsPort
from shared.tracing.tracer import trace_span

class QualityBaselineService:
    @staticmethod
    def recompute_and_update_redis(
        postgres: PostgresPort, redis: RedisPort, metrics: MetricsPort
    ) -> int:
        with trace_span("quality_baseline.recompute_and_update_redis") as span:
            start_time = datetime.now()
            baselines = postgres.get_rolling_baselines()
            span.set_attribute("baselines_count", len(baselines))
            
            for b in baselines:
                redis.set_baseline_quality(
                    model=b.model,
                    endpoint=b.endpoint,
                    prompt_type=b.prompt_type,
                    score=b.avg_score
                )
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            metrics.record_workflow_run_latency("recompute_quality_baseline", duration_ms)
            metrics.record_baseline_updates(len(baselines))
            return len(baselines)

    @staticmethod
    def rollup_yesterday_scores(
        postgres: PostgresPort, clickhouse: ClickHousePort, metrics: MetricsPort, target_date: datetime | None = None
    ) -> int:
        with trace_span("quality_baseline.rollup_yesterday_scores") as span:
            start_time = datetime.now()
            
            ref_date = target_date or datetime.now(timezone.utc)
            yesterday = (ref_date - timedelta(days=1)).date()
            span.set_attribute("target_date", yesterday.isoformat())
            
            start_bound = datetime.combine(yesterday, time.min).replace(tzinfo=timezone.utc)
            end_bound = datetime.combine(yesterday, time.max).replace(tzinfo=timezone.utc)
            
            rollup_data = postgres.get_daily_rollup_data(start_bound, end_bound)
            span.set_attribute("rollup_rows_count", len(rollup_data))
            
            ch_rows = []
            for r in rollup_data:
                ch_rows.append((
                    r.rollup_date,
                    r.model,
                    r.endpoint,
                    r.prompt_type,
                    r.avg_composite_score,
                    r.flag_count,
                    r.sample_count
                ))
            
            if ch_rows:
                clickhouse.insert_quality_trends(ch_rows)
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            metrics.record_workflow_run_latency("rollup_quality_trend", duration_ms)
            metrics.record_rollup_rows(len(ch_rows))
            return len(ch_rows)
