from __future__ import annotations
import os
import re
import json
import base64
import logging
from datetime import datetime, timezone
import yaml
from ddsketch import DDSketch
from ddsketch.pb import ddsketch_pb2
from ddsketch.pb.proto import DDSketchProto
import redis

from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger(__name__)

class LatencyHandler:
    def __init__(self, redis_client: redis.Redis, slo_config_path: str):
        self.redis = redis_client
        self.slo_config_path = slo_config_path
        self.slo_config = self._load_slo_config()
        self.redis_buffer: dict[str, list[float]] = {}
        self.redis_down_since: datetime | None = None

    def _load_slo_config(self) -> dict:
        try:
            if os.path.exists(self.slo_config_path):
                with open(self.slo_config_path, "r") as f:
                    return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error("Failed to load SLO config: %s", e)
        return {}

    def get_slo_threshold(self, endpoint: str) -> float:
        endpoints = self.slo_config.get("endpoints", {})
        return endpoints.get(endpoint, endpoints.get("default", 500.0))

    def _serialize_sketch(self, sketch: DDSketch) -> str:
        proto_msg = DDSketchProto.to_proto(sketch)
        binary_data = proto_msg.SerializeToString()
        return base64.b64encode(binary_data).decode('utf-8')

    def _deserialize_sketch(self, b64_str: str) -> DDSketch:
        binary_data = base64.b64decode(b64_str)
        proto_msg = ddsketch_pb2.DDSketch()
        proto_msg.ParseFromString(binary_data)
        return DDSketchProto.from_proto(proto_msg)

    def _update_sketch_key_direct(self, key: str, values: list[float]) -> bool:
        try:
            b64_data = self.redis.get(key)
            if b64_data:
                try:
                    sketch = self._deserialize_sketch(b64_data.decode('utf-8'))
                except Exception as e:
                    logger.error("Failed to deserialize sketch for key %s during direct update: %s", key, e)
                    sketch = DDSketch(relative_accuracy=0.01)
            else:
                sketch = DDSketch(relative_accuracy=0.01)

            for val in values:
                sketch.add(val)

            serialized = self._serialize_sketch(sketch)
            self.redis.set(key, serialized)
            return True
        except Exception as e:
            logger.warning("Direct sketch update failed for key %s: %s", key, e)
            return False

    def _replay_buffer(self):
        logger.info("Redis recovered. Replaying %s buffered sketch keys.", len(self.redis_buffer))
        keys_to_remove = []
        for key, values in self.redis_buffer.items():
            success = self._update_sketch_key_direct(key, values)
            if success:
                keys_to_remove.append(key)
            else:
                break
        for key in keys_to_remove:
            del self.redis_buffer[key]

    def _buffer_values(self, key: str, values: list[float]):
        self.redis_buffer.setdefault(key, []).extend(values)
        total_buffered = sum(len(v) for v in self.redis_buffer.values())
        
        if self.redis_down_since is not None:
            elapsed = (datetime.now() - self.redis_down_since).total_seconds()
            if elapsed > 60.0 and total_buffered > 1000:
                to_drop = total_buffered - 1000
                dropped_count = 0
                for k in list(self.redis_buffer.keys()):
                    vals = self.redis_buffer[k]
                    if len(vals) <= to_drop - dropped_count:
                        dropped_count += len(vals)
                        del self.redis_buffer[k]
                    else:
                        self.redis_buffer[k] = vals[to_drop - dropped_count:]
                        dropped_count = to_drop
                        break
                logger.error("latency_sketch_dropped_total count=%s", dropped_count)

    def _update_sketch_key(self, key: str, values: list[float]) -> bool:
        if self.redis_down_since is not None:
            self._buffer_values(key, values)
            return False

        try:
            success = self._update_sketch_key_direct(key, values)
            if not success:
                raise redis.exceptions.ConnectionError("Redis direct update returned False")
            return True
        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
            logger.warning("Redis connection failed during sketch update for key %s, buffering: %s", key, e)
            if self.redis_down_since is None:
                self.redis_down_since = datetime.now()
            self._buffer_values(key, values)
            return False

    def handle_spans(self, spans: list[dict]):
        tracer = trace.get_tracer("latency-engine")
        with tracer.start_as_current_span("latency_handler.handle_spans", attributes={"batch.size": len(spans)}) as batch_span:
            # Check Redis recovery
            if self.redis_down_since is not None:
                try:
                    self.redis.ping()
                    self.redis_down_since = None
                    self._replay_buffer()
                except Exception:
                    pass

            sketch_updates: dict[str, list[float]] = {}
            pipe = None
            try:
                if self.redis_down_since is None:
                    pipe = self.redis.pipeline()
            except Exception:
                pass

            for span in spans:
                try:
                    model = span.get("model")
                    if not model:
                        continue
                    
                    endpoint = span.get("endpoint", "default")
                    span_id = span.get("span_id")
                    finish_reason = span.get("finish_reason")
                    retry_count = span.get("retry_count", 0) or 0
                    completion_tokens = span.get("completion_tokens", 0) or 0
                    
                    latency_ms_ttft = span.get("latency_ms_ttft")
                    latency_ms_total = span.get("latency_ms_total")
                    timestamp_utc_str = span.get("timestamp_utc")

                    # Extract context
                    traceparent = span.get("_traceparent")
                    tracestate = span.get("_tracestate")
                    parent_ctx = None
                    if traceparent:
                        carrier = {"traceparent": traceparent}
                        if tracestate:
                            carrier["tracestate"] = tracestate
                        parent_ctx = TraceContextTextMapPropagator().extract(carrier)

                    # Extract latency attribution tags for OTEL span recording
                    attributes = span.get("attributes", {}) or {}
                    dns_latency = attributes.get("net.dns.latency_ms")
                    tcp_latency = attributes.get("net.tcp.latency_ms")
                    queue_latency = attributes.get("llm.queue.latency_ms")
                    inference_latency = attributes.get("llm.inference.latency_ms")

                    with tracer.start_as_current_span(
                        "latency_handler.process_span",
                        context=parent_ctx,
                        attributes={
                            "span_id": span_id or "unknown",
                            "model": model or "unknown",
                            "endpoint": endpoint or "default",
                            "net.dns.latency_ms": float(dns_latency) if dns_latency is not None else 0.0,
                            "net.tcp.latency_ms": float(tcp_latency) if tcp_latency is not None else 0.0,
                            "llm.queue.latency_ms": float(queue_latency) if queue_latency is not None else 0.0,
                            "llm.inference.latency_ms": float(inference_latency) if inference_latency is not None else 0.0,
                        }
                    ) as item_span:
                        if latency_ms_total is None:
                            continue

                        # Parse timestamp
                        try:
                            ts_str = timestamp_utc_str.replace("Z", "+00:00")
                            dt = datetime.fromisoformat(ts_str)
                        except Exception:
                            dt = datetime.now(timezone.utc)
                        hour_of_day = dt.astimezone(timezone.utc).hour
                        unix_ts = int(dt.timestamp())

                        # F-L-01 & F-L-05: DDSketch updates
                        if latency_ms_ttft is not None:
                            ttft_key = f"sketch:ttft:{model}:{hour_of_day}"
                            sketch_updates.setdefault(ttft_key, []).append(float(latency_ms_ttft))

                        if retry_count > 0:
                            retry_key = f"sketch:total:retry:{model}"
                            sketch_updates.setdefault(retry_key, []).append(float(latency_ms_total))
                        else:
                            total_key = f"sketch:total:{model}:{endpoint}:{hour_of_day}"
                            sketch_updates.setdefault(total_key, []).append(float(latency_ms_total))

                        # F-L-02: TPOT computation
                        if (latency_ms_ttft is not None and 
                            completion_tokens > 0 and 
                            finish_reason != "timeout"):
                            tpot_ms = (latency_ms_total - latency_ms_ttft) / completion_tokens
                            tpot_key = f"tpot:latest:{model}"
                            if pipe:
                                pipe.lpush(tpot_key, tpot_ms)
                                pipe.ltrim(tpot_key, 0, 999)

                        # F-L-03: SLO error counter update
                        threshold = self.get_slo_threshold(endpoint)
                        minute_bucket = unix_ts // 60
                        
                        slo_total_key = f"slo:total:{model}:{endpoint}:{minute_bucket}"
                        if pipe:
                            pipe.incr(slo_total_key)
                            pipe.expire(slo_total_key, 21600)
                        
                        if latency_ms_total > threshold:
                            slo_err_key = f"slo:errors:{model}:{endpoint}:{minute_bucket}"
                            if pipe:
                                pipe.incr(slo_err_key)
                                pipe.expire(slo_err_key, 21600)

                        # F-L-04: Latency attribution tag extraction
                        attr_data = {}
                        if dns_latency is not None:
                            attr_data["dns"] = float(dns_latency)
                        if tcp_latency is not None:
                            attr_data["tcp"] = float(tcp_latency)
                        if queue_latency is not None:
                            attr_data["queue"] = float(queue_latency)
                        if inference_latency is not None:
                            attr_data["inference"] = float(inference_latency)

                        if attr_data and span_id:
                            attr_key = f"attribution:{span_id}"
                            if pipe:
                                pipe.hset(attr_key, mapping={k: str(v) for k, v in attr_data.items()})
                                pipe.expire(attr_key, 300)
                            
                            hour_str = dt.astimezone(timezone.utc).strftime("%Y%m%d%H")
                            agg_key = f"attr:avg:{model}:{hour_str}"
                            for attr_name, val in attr_data.items():
                                if pipe:
                                    pipe.hincrbyfloat(agg_key, attr_name, val)
                                    pipe.expire(agg_key, 604800)

                except Exception as e:
                    logger.error("Error processing span: %s", e)

            # Execute pipeline
            if pipe:
                try:
                    pipe.execute()
                except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
                    logger.warning("Pipeline execution failed (Redis down): %s", e)
                    if self.redis_down_since is None:
                        self.redis_down_since = datetime.now()
                except Exception as e:
                    logger.error("Pipeline execution failed: %s", e)

            # Update DDSketch metrics
            for key, values in sketch_updates.items():
                self._update_sketch_key(key, values)

