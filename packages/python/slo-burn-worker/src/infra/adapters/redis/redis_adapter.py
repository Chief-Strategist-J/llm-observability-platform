import base64
import logging
import redis
from typing import List, Tuple
from ddsketch.pb import ddsketch_pb2
from ddsketch.pb.proto import DDSketchProto
from shared.ports.redis_port import RedisPort
from shared.tracing.tracer import trace_span

logger = logging.getLogger(__name__)

class RedisAdapter(RedisPort):
    def __init__(self, url: str):
        self.client = redis.from_url(url)

    def scan_slo_keys(self) -> List[Tuple[str, str]]:
        with trace_span("redis:scan_slo_keys", attributes={"db.system": "redis"}):
            pairs = set()
            # Scan for slo:total:* keys
            for key in self.client.scan_iter("slo:total:*"):
                try:
                    key_str = key.decode("utf-8")
                    parts = key_str.split(":")
                    if len(parts) >= 5:
                        model = parts[2]
                        endpoint = parts[3]
                        pairs.add((model, endpoint))
                except Exception as e:
                    logger.warning("Failed to parse Redis slo key %s: %s", key, e)
            return list(pairs)

    def get_slo_buckets(
        self, model: str, endpoint: str, buckets: List[int]
    ) -> Tuple[List[int], List[int]]:
        if not buckets:
            return [], []
        with trace_span(
            "redis:get_slo_buckets",
            attributes={
                "db.system": "redis",
                "model": model,
                "endpoint": endpoint,
            },
        ):
            err_keys = [f"slo:errors:{model}:{endpoint}:{b}" for b in buckets]
            tot_keys = [f"slo:total:{model}:{endpoint}:{b}" for b in buckets]
            
            # MGET values
            err_vals = self.client.mget(err_keys)
            tot_vals = self.client.mget(tot_keys)
            
            errors = [int(v) if v is not None else 0 for v in err_vals]
            totals = [int(v) if v is not None else 0 for v in tot_vals]
            
            return errors, totals

    def write_burn_rate(
        self, window: str, model: str, endpoint: str, burn_rate: float, ttl: int
    ) -> None:
        with trace_span(
            "redis:write_burn_rate",
            attributes={
                "db.system": "redis",
                "window": window,
                "model": model,
                "endpoint": endpoint,
            },
        ):
            key = f"slo:burn:{window}:{model}:{endpoint}"
            self.client.setex(key, ttl, str(burn_rate))

    def check_and_set_dedup_lock(
        self, model: str, endpoint: str, severity: str, ttl: int
    ) -> bool:
        with trace_span(
            "redis:check_and_set_dedup_lock",
            attributes={
                "db.system": "redis",
                "model": model,
                "endpoint": endpoint,
                "severity": severity,
            },
        ):
            key = f"rate_limit:latency_alert:{model}:{endpoint}:{severity}"
            # Set if not exists (NX) with expiration (EX)
            result = self.client.set(key, "1", ex=ttl, nx=True)
            return bool(result)

    def write_budget_remaining(
        self, model: str, endpoint: str, budget_remaining_pct: float, ttl: int
    ) -> None:
        with trace_span(
            "redis:write_budget_remaining",
            attributes={
                "db.system": "redis",
                "model": model,
                "endpoint": endpoint,
            },
        ):
            key = f"slo:budget_remaining:{model}:{endpoint}"
            self.client.setex(key, ttl, str(budget_remaining_pct))

    def get_ddsketch_percentiles(
        self, model: str, endpoint: str, hour_of_day: int
    ) -> Tuple[float, float]:
        with trace_span(
            "redis:get_ddsketch_percentiles",
            attributes={
                "db.system": "redis",
                "model": model,
                "endpoint": endpoint,
                "hour_of_day": hour_of_day,
            },
        ):
            key = f"sketch:total:{model}:{endpoint}:{hour_of_day}"
            b64_data = self.client.get(key)
            if not b64_data:
                return 0.0, 0.0
            try:
                val_str = b64_data.decode("utf-8") if isinstance(b64_data, bytes) else b64_data
                binary_data = base64.b64decode(val_str)
                proto_msg = ddsketch_pb2.DDSketch()
                proto_msg.ParseFromString(binary_data)
                sketch = DDSketchProto.from_proto(proto_msg)  # type: ignore[no-untyped-call]
                p95 = sketch.get_quantile_value(0.95)
                p99 = sketch.get_quantile_value(0.99)
                return float(p95), float(p99)
            except Exception as e:
                logger.warning("Failed to deserialize DDSketch for key %s: %s", key, e)
                return 0.0, 0.0
