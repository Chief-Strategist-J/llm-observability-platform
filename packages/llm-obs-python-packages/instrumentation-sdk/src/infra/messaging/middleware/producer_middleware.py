from typing import Callable, Any, Dict, Optional, Set
import time
import json
import random
import logging
import hashlib
from src.infra.messaging.middleware.pipeline import ProduceCtx
from src.infra.messaging.tracing.messaging_tracer import messaging_tracer

logger = logging.getLogger("kafka.producer.middleware")

def with_tracing_producer(ctx: ProduceCtx, next_fn: Callable[[ProduceCtx], None]) -> None:
    event_name = ctx.metadata.get("event_name", "LLMSpan")
    with messaging_tracer.start_producer_span(
        topic=ctx.topic,
        event_name=event_name,
        correlation_id=ctx.correlation_id,
        tenant_id=ctx.tenant_id,
    ) as span:
        messaging_tracer.inject_context(headers=ctx.headers)
        ctx.headers["x-correlation-id"] = ctx.correlation_id
        ctx.headers["x-tenant-id"] = ctx.tenant_id
        next_fn(ctx)

class TopicCircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_time_sec: float = 30.0) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_time_sec = recovery_time_sec
        self._failures: Dict[str, int] = {}
        self._open_since: Dict[str, float] = {}

    def is_open(self, topic: str) -> bool:
        if topic in self._open_since:
            if time.time() - self._open_since[topic] > self.recovery_time_sec:
                del self._open_since[topic]
                self._failures[topic] = 0
                return False
            return True
        return False

    def record_success(self, topic: str) -> None:
        self._failures[topic] = 0
        self._open_since.pop(topic, None)

    def record_failure(self, topic: str) -> None:
        self._failures[topic] = self._failures.get(topic, 0) + 1
        if self._failures[topic] >= self.failure_threshold:
            self._open_since[topic] = time.time()
            logger.warning(f"Circuit breaker OPEN for topic: {topic}")

global_circuit_breaker = TopicCircuitBreaker()

def with_circuit_breaker_producer(
    breaker: Optional[TopicCircuitBreaker] = None,
) -> Callable[[ProduceCtx, Callable[[ProduceCtx], None]], None]:
    cb = breaker or global_circuit_breaker

    def _middleware(ctx: ProduceCtx, next_fn: Callable[[ProduceCtx], None]) -> None:
        if cb.is_open(ctx.topic):
            raise RuntimeError(f"Circuit breaker is OPEN for topic {ctx.topic}")
        try:
            next_fn(ctx)
            cb.record_success(ctx.topic)
        except Exception as err:
            cb.record_failure(ctx.topic)
            raise err

    return _middleware

def with_retry_producer(
    max_attempts: int = 5,
    base_delay_sec: float = 0.1,
) -> Callable[[ProduceCtx, Callable[[ProduceCtx], None]], None]:

    def _middleware(ctx: ProduceCtx, next_fn: Callable[[ProduceCtx], None]) -> None:
        attempt = 0
        while True:
            remaining_sec = ctx.deadline - time.time() if ctx.deadline > 0 else 30.0
            if remaining_sec <= 0:
                raise TimeoutError("Outbound produce deadline budget exceeded")

            try:
                return next_fn(ctx)
            except Exception as err:
                attempt += 1
                if attempt >= max_attempts:
                    raise err

                exponential_delay = min(base_delay_sec * (2 ** attempt), remaining_sec)
                jittered_delay = random.uniform(0, exponential_delay)
                time.sleep(jittered_delay)

    return _middleware

class DedupeStore:
    def __init__(self) -> None:
        self._seen: Set[str] = set()

    def set_if_absent(self, key: str) -> bool:
        if key in self._seen:
            return False
        self._seen.add(key)
        return True

    def remove(self, key: str) -> None:
        self._seen.discard(key)

global_dedupe_store = DedupeStore()

def with_idempotence_guard(
    store: Optional[DedupeStore] = None,
) -> Callable[[ProduceCtx, Callable[[ProduceCtx], None]], None]:
    dedupe = store or global_dedupe_store

    def _middleware(ctx: ProduceCtx, next_fn: Callable[[ProduceCtx], None]) -> None:
        payload_bytes = str(ctx.payload).encode("utf-8")
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()[:16]
        dedupe_key = ctx.headers.get("idempotency_key") or f"{ctx.topic}:{ctx.key}:{payload_hash}"

        if not dedupe.set_if_absent(dedupe_key):
            logger.info(f"Duplicate publish suppressed for key: {dedupe_key}")
            return

        try:
            next_fn(ctx)
        except Exception as err:
            dedupe.remove(dedupe_key)
            raise err

    return _middleware

def with_schema_validation(
    validator_fn: Optional[Callable[[Any], bool]] = None,
) -> Callable[[ProduceCtx, Callable[[ProduceCtx], None]], None]:

    def _middleware(ctx: ProduceCtx, next_fn: Callable[[ProduceCtx], None]) -> None:
        if validator_fn:
            is_valid = validator_fn(ctx.payload)
            if not is_valid:
                raise ValueError(f"Schema validation failed for payload on topic {ctx.topic}")
        ctx.headers["schema_version"] = "1"
        next_fn(ctx)

    return _middleware

def with_serialization(
    encoder_fn: Optional[Callable[[Any], bytes]] = None,
) -> Callable[[ProduceCtx, Callable[[ProduceCtx], None]], None]:
    encode = encoder_fn or (lambda val: json.dumps(val).encode("utf-8") if isinstance(val, (dict, list)) else (val.encode("utf-8") if isinstance(val, str) else val))

    def _middleware(ctx: ProduceCtx, next_fn: Callable[[ProduceCtx], None]) -> None:
        serialized_payload = encode(ctx.payload)
        ctx.payload = serialized_payload
        next_fn(ctx)

    return _middleware

def with_partition_key_selection(
    key_strategy: Callable[[ProduceCtx], str],
) -> Callable[[ProduceCtx, Callable[[ProduceCtx], None]], None]:

    def _middleware(ctx: ProduceCtx, next_fn: Callable[[ProduceCtx], None]) -> None:
        ctx.key = key_strategy(ctx)
        if not ctx.key:
            raise ValueError(f"Partition key strategy generated empty key for topic {ctx.topic}")
        next_fn(ctx)

    return _middleware
