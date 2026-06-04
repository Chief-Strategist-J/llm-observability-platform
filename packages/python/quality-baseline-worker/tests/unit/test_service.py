from datetime import datetime, date, timezone
from features.quality_baseline.service import QualityBaselineService
from features.quality_baseline.types import BaselineRecomputeResult, DailyRollupRecord

class MockPostgres:
    def __init__(self, baselines, rollup_data):
        self.baselines = baselines
        self.rollup_data = rollup_data

    def get_rolling_baselines(self):
        return self.baselines

    def get_daily_rollup_data(self, start_time, end_time):
        return self.rollup_data

class MockRedis:
    def __init__(self):
        self.calls = []

    def set_baseline_quality(self, model, endpoint, prompt_type, score):
        self.calls.append((model, endpoint, prompt_type, score))

class MockClickHouse:
    def __init__(self):
        self.calls = []

    def insert_quality_trends(self, rows):
        self.calls.extend(rows)

class MockMetrics:
    def __init__(self):
        self.latency_calls = []
        self.updates_calls = []
        self.rollup_calls = []

    def record_workflow_run_latency(self, workflow_name, latency_ms):
        self.latency_calls.append((workflow_name, latency_ms))

    def record_baseline_updates(self, count):
        self.updates_calls.append(count)

    def record_rollup_rows(self, count):
        self.rollup_calls.append(count)

def test_recompute_and_update_redis() -> None:
    baselines = [
        BaselineRecomputeResult(model="m1", endpoint="e1", prompt_type="p1", avg_score=0.85, sample_count=10)
    ]
    pg = MockPostgres(baselines, [])
    redis = MockRedis()
    metrics = MockMetrics()

    count = QualityBaselineService.recompute_and_update_redis(pg, redis, metrics)
    assert count == 1
    assert redis.calls == [("m1", "e1", "p1", 0.85)]
    assert metrics.updates_calls == [1]

def test_rollup_yesterday_scores() -> None:
    target_date = datetime(2026, 6, 4, tzinfo=timezone.utc)
    rollup_data = [
        DailyRollupRecord(
            rollup_date=date(2026, 6, 3),
            model="m1",
            endpoint="e1",
            prompt_type="p1",
            avg_composite_score=0.9,
            flag_count=2,
            sample_count=20
        )
    ]
    pg = MockPostgres([], rollup_data)
    ch = MockClickHouse()
    metrics = MockMetrics()

    count = QualityBaselineService.rollup_yesterday_scores(pg, ch, metrics, target_date=target_date)
    assert count == 1
    assert ch.calls == [(date(2026, 6, 3), "m1", "e1", "p1", 0.9, 2, 20)]
    assert metrics.rollup_calls == [1]
