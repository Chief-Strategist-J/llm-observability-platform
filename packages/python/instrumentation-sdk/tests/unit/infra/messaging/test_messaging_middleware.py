import unittest
import time
from src.infra.messaging.middleware import (
    ProduceCtx,
    ConsumeCtx,
    ProducerMiddlewarePipeline,
    ConsumerMiddlewarePipeline,
    with_tracing_producer,
    with_circuit_breaker_producer,
    with_retry_producer,
    with_idempotence_guard,
    with_schema_validation,
    with_serialization,
    with_partition_key_selection,
    with_tracing_consumer,
    with_deserialization,
    with_retry_count_header,
    with_dlq_on_failure,
    with_tenant_context,
    with_concurrency_limit,
    with_heartbeat_during_processing,
    TopicCircuitBreaker,
    DedupeStore,
)

class TestMessagingMiddleware(unittest.TestCase):

    def test_producer_pipeline_composition(self):
        executed_steps = []

        def target_produce(ctx: ProduceCtx):
            executed_steps.append("target_produce")
            self.assertEqual(ctx.headers.get("x-tenant-id"), "tenant-123")
            self.assertIsInstance(ctx.payload, bytes)

        def key_strategy(ctx: ProduceCtx) -> str:
            return f"{ctx.tenant_id}:key1"

        pipeline = ProducerMiddlewarePipeline([
            with_tracing_producer,
            with_idempotence_guard(DedupeStore()),
            with_schema_validation(lambda p: True),
            with_serialization(),
            with_partition_key_selection(key_strategy),
        ])

        ctx = ProduceCtx(
            topic="test.events.v1",
            key="",
            payload={"span_id": "span-1", "model": "gpt-4o"},
            tenant_id="tenant-123",
            correlation_id="corr-456",
            deadline=time.time() + 10.0,
        )

        pipeline.execute(ctx, target_produce)
        self.assertIn("target_produce", executed_steps)
        self.assertEqual(ctx.key, "tenant-123:key1")

    def test_producer_circuit_breaker(self):
        cb = TopicCircuitBreaker(failure_threshold=2, recovery_time_sec=10.0)
        pipeline = ProducerMiddlewarePipeline([
            with_circuit_breaker_producer(cb)
        ])

        def failing_target(ctx: ProduceCtx):
            raise RuntimeError("Broker connection failed")

        ctx = ProduceCtx(topic="test.broken.v1", key="k", payload="data")

        with self.assertRaises(RuntimeError):
            pipeline.execute(ctx, failing_target)

        with self.assertRaises(RuntimeError):
            pipeline.execute(ctx, failing_target)

        self.assertTrue(cb.is_open("test.broken.v1"))
        with self.assertRaises(RuntimeError) as cm:
            pipeline.execute(ctx, failing_target)
        self.assertIn("Circuit breaker is OPEN", str(cm.exception))

    def test_consumer_pipeline_execution(self):
        executed_steps = []

        class MockRawMessage:
            def __init__(self, value):
                self.value = value

        def domain_handler(ctx: ConsumeCtx):
            executed_steps.append("domain_handler")
            self.assertEqual(ctx.tenant_id, "tenant-abc")
            self.assertEqual(ctx.payload.get("status"), "ok")
            return "SUCCESS"

        pipeline = ConsumerMiddlewarePipeline([
            with_tracing_consumer,
            with_deserialization(),
            with_retry_count_header,
            with_tenant_context,
            with_concurrency_limit(max_concurrent=5),
        ])

        raw_msg = MockRawMessage(b'{"status": "ok", "tenant_id": "tenant-abc"}')
        ctx = ConsumeCtx(
            topic="test.consumed.v1",
            partition=0,
            offset="100",
            raw_message=raw_msg,
            headers={"tenant_id": "tenant-abc", "x-retry-count": "1"},
        )

        result = pipeline.execute(ctx, domain_handler)
        self.assertEqual(result, "SUCCESS")
        self.assertIn("domain_handler", executed_steps)
        self.assertEqual(ctx.attempt, 1)

    def test_consumer_dlq_routing(self):
        dlq_records = []

        def dlq_publisher(ctx: ConsumeCtx, err: Exception):
            dlq_records.append((ctx.topic, ctx.offset, str(err)))

        pipeline = ConsumerMiddlewarePipeline([
            with_dlq_on_failure(max_attempts=2, dlq_publisher_fn=dlq_publisher)
        ])

        def failing_handler(ctx: ConsumeCtx):
            raise ValueError("Poison payload format")

        ctx = ConsumeCtx(
            topic="test.poison.v1",
            partition=0,
            offset="500",
            raw_message=None,
            attempt=2,
        )

        result = pipeline.execute(ctx, failing_handler)
        self.assertIsNone(result)
        self.assertEqual(len(dlq_records), 1)
        self.assertEqual(dlq_records[0][0], "test.poison.v1")

if __name__ == "__main__":
    unittest.main()
