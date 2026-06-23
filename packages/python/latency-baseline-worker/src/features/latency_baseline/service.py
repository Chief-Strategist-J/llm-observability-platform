from datetime import datetime, timezone, timedelta, date, time
import json
import logging
import base64
from ddsketch import DDSketch
from ddsketch.pb import ddsketch_pb2
from ddsketch.pb.proto import DDSketchProto
from shared.ports.clickhouse_port import ClickHousePort
from shared.ports.redis_port import RedisPort
from shared.ports.kafka_producer_port import KafkaProducerPort
from shared.tracing.tracer import trace_span

logger = logging.getLogger(__name__)

def median(lst: list[float]) -> float:
    n = len(lst)
    if n == 0:
        return 0.0
    s = sorted(lst)
    if n % 2 == 1:
        return s[n // 2]
    else:
        return (s[n // 2 - 1] + s[n // 2]) / 2.0

class LatencyBaselineService:
    @staticmethod
    def deserialize_sketch(b64_str: str) -> DDSketch:
        binary_data = base64.b64decode(b64_str)
        proto_msg = ddsketch_pb2.DDSketch()
        proto_msg.ParseFromString(binary_data)
        return DDSketchProto.from_proto(proto_msg)

    @staticmethod
    def run_hourly_checkpoint(
        redis: RedisPort,
        clickhouse: ClickHousePort,
        kafka: KafkaProducerPort,
        target_date: date | None = None,
        target_hour: int | None = None
    ) -> int:
        with trace_span("latency_baseline.run_hourly_checkpoint") as span:
            # 1. Determine target date and hour
            now_utc = datetime.now(timezone.utc)
            if target_hour is None:
                prior_time = now_utc - timedelta(hours=1)
                target_date = prior_time.date()
                target_hour = prior_time.hour
            elif target_date is None:
                target_date = now_utc.date()

            span.set_attribute("target_date", target_date.isoformat())
            span.set_attribute("target_hour", target_hour)

            # Construct hour timestamp for SLO queries
            dt = datetime.combine(target_date, time(hour=target_hour)).replace(tzinfo=timezone.utc)
            hour_timestamp = int(dt.timestamp())

            # 2. Identify active model+hour keys in Redis
            # Pattern: sketch:ttft:{model}:{hour_of_day}
            ttft_pattern = f"sketch:ttft:*:{target_hour}"
            ttft_keys = redis.scan_keys(ttft_pattern)
            
            models = set()
            for key in ttft_keys:
                parts = key.split(":")
                if len(parts) >= 4:
                    model = parts[2]
                    models.add(model)

            logger.info("Found %s active models for hour %s", len(models), target_hour)

            records_to_insert = []
            checkpoint_time = datetime.now(timezone.utc)

            for model in models:
                # Get TTFT sketch
                ttft_key = f"sketch:ttft:{model}:{target_hour}"
                ttft_b64 = redis.get_key(ttft_key)
                if not ttft_b64:
                    continue

                try:
                    ttft_sketch = LatencyBaselineService.deserialize_sketch(ttft_b64)
                    p50_ttft = ttft_sketch.get_quantile_value(0.50)
                    p95_ttft = ttft_sketch.get_quantile_value(0.95)
                    p99_ttft = ttft_sketch.get_quantile_value(0.99)
                except Exception as e:
                    logger.error("Failed to deserialize TTFT sketch for model %s: %s", model, e)
                    continue

                # Find all endpoints for this model and hour
                # Pattern: sketch:total:{model}:{endpoint}:{hour_of_day}
                total_pattern = f"sketch:total:{model}:*:{target_hour}"
                total_keys = redis.scan_keys(total_pattern)

                if not total_keys:
                    # Try fallback to no endpoint if it exists
                    fallback_key = f"sketch:total:{model}:{target_hour}"
                    total_keys = [fallback_key] if redis.get_key(fallback_key) else []

                for key in total_keys:
                    # Extract endpoint
                    parts = key.split(":")
                    if len(parts) == 5:
                        endpoint = parts[3]
                    else:
                        endpoint = "default"

                    total_b64 = redis.get_key(key)
                    if not total_b64:
                        continue

                    try:
                        total_sketch = LatencyBaselineService.deserialize_sketch(total_b64)
                        p50_total = total_sketch.get_quantile_value(0.50)
                        p95_total = total_sketch.get_quantile_value(0.95)
                        p99_total = total_sketch.get_quantile_value(0.99)
                        sample_count = total_sketch.count
                    except Exception as e:
                        logger.error("Failed to deserialize Total sketch for key %s: %s", key, e)
                        continue

                    # Fetch SLO violation count
                    slo_violation_count = redis.get_slo_violation_count(model, endpoint, hour_timestamp)

                    records_to_insert.append((
                        model,
                        endpoint,
                        target_date,
                        target_hour,
                        float(p50_ttft),
                        float(p95_ttft),
                        float(p99_ttft),
                        float(p50_total),
                        float(p95_total),
                        float(p99_total),
                        int(sample_count),
                        int(slo_violation_count),
                        checkpoint_time
                    ))

            # 3. Write checkpoints to ClickHouse
            if records_to_insert:
                clickhouse.insert_latency_checkpoints(records_to_insert)
                logger.info("Inserted %s checkpoints to ClickHouse", len(records_to_insert))

                # 4. TTFT regression check (F-L-12)
                for r in records_to_insert:
                    model, endpoint, _, hour_of_day, _, _, current_p99, _, _, _, sample_count, _, _ = r
                    
                    # Fetch last 7 days history from ClickHouse
                    history = clickhouse.get_p99_ttft_history_7d(model, endpoint, hour_of_day)
                    
                    # Compute baseline (median of last 7 values)
                    # Note: ClickHouse history includes the current written value since we just inserted it.
                    # To get prior values, we exclude the first element if it matches the current written checkpoint timestamp/value,
                    # or simply take the next 7 values.
                    # Let's filter or slice the history to get the prior 7 points.
                    prior_history = history[1:8] if len(history) > 1 else []
                    
                    # Check for cold start suppression
                    if len(prior_history) < 7:
                        logger.info("TTFT regression check suppressed for model=%s endpoint=%s due to cold start (fewer than 7 prior data points: %s)", model, endpoint, len(prior_history))
                        continue

                    baseline_p99_ttft = median(prior_history)
                    redis.set_baseline_p99_ttft(model, endpoint, hour_of_day, baseline_p99_ttft)

                    if current_p99 > 2 * baseline_p99_ttft and sample_count >= 30:
                        alert_payload = {
                            "model": model,
                            "endpoint": endpoint,
                            "hour_of_day": hour_of_day,
                            "current_p99_ttft": current_p99,
                            "baseline_p99_ttft": baseline_p99_ttft,
                            "sample_count": sample_count,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        kafka.produce(
                            topic="alerts.latency.ttft_regression",
                            key=f"{model}:{endpoint}",
                            value=json.dumps(alert_payload).encode("utf-8")
                        )
                        logger.warning("TTFT Regression Alert produced: %s", alert_payload)
                
                kafka.flush()

            # 5. Sketch rotation check (F-L-13)
            # Verify expected sketches exist for current and prior hour.
            current_hour = now_utc.hour
            prior_hour = (now_utc - timedelta(hours=1)).hour

            # Collect active models from all sketches in Redis
            all_ttft_keys = redis.scan_keys("sketch:ttft:*")
            active_models = set()
            for key in all_ttft_keys:
                parts = key.split(":")
                if len(parts) >= 3:
                    active_models.add(parts[2])

            for model in active_models:
                for h in [current_hour, prior_hour]:
                    key = f"sketch:ttft:{model}:{h}"
                    # Check if key exists in Redis
                    val = redis.get_key(key)
                    if not val:
                        logger.error("sketch_missing_total{model=%s, hour=%s}", model, h)

            return len(records_to_insert)
