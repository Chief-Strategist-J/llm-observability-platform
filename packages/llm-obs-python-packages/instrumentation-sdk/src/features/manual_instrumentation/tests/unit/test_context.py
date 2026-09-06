import unittest
import asyncio
import time
from typing import Any, Dict
from src.features.manual_instrumentation.service import llm_span
from src.features.spans.globals import set_reporter

class MockReporter:
    def __init__(self):
        self.spans = []

    def report(self, span_data: Dict[str, Any]) -> None:
        self.spans.append(span_data)

    async def report_async(self, span_data: Dict[str, Any]) -> None:
        self.spans.append(span_data)

class TestManualInstrumentation(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.reporter = MockReporter()
        set_reporter(self.reporter)

    def test_sync_context_manager(self):
        with llm_span(model="gpt-4o", service_name="test-service") as span:
            span.set_metadata("user_id", "user-123")
            time.sleep(0.01)
        
        self.assertEqual(len(self.reporter.spans), 1)
        span_data = self.reporter.spans[0]
        self.assertEqual(span_data["model"], "gpt-4o")
        self.assertEqual(span_data["service_name"], "test-service")
        self.assertEqual(span_data["user_id"], "user-123")
        self.assertEqual(span_data["status"], "success")
        self.assertGreaterEqual(span_data["latency_ms_total"], 10)

    async def test_async_context_manager(self):
        async with llm_span(model="gpt-4o-async", service_name="test-service-async") as span:
            span.set_metadata("session_id", "sess-456")
            await asyncio.sleep(0.01)
        
        self.assertEqual(len(self.reporter.spans), 1)
        span_data = self.reporter.spans[0]
        self.assertEqual(span_data["model"], "gpt-4o-async")
        self.assertEqual(span_data["session_id"], "sess-456")
        self.assertEqual(span_data["status"], "success")
        self.assertGreaterEqual(span_data["latency_ms_total"], 10)

    def test_sync_error_handling(self):
        try:
            with llm_span(model="gpt-4o", service_name="test-error") as span:
                raise ValueError("test error")
        except ValueError:
            pass
        
        self.assertEqual(len(self.reporter.spans), 1)
        span_data = self.reporter.spans[0]
        self.assertEqual(span_data["status"], "error")

    async def test_async_error_handling(self):
        try:
            async with llm_span(model="gpt-4o", service_name="test-error-async") as span:
                raise ValueError("test error async")
        except ValueError:
            pass
        
        self.assertEqual(len(self.reporter.spans), 1)
        span_data = self.reporter.spans[0]
        self.assertEqual(span_data["status"], "error")

    async def test_nested_spans(self):
        async with llm_span(model="parent", service_name="parent-service") as parent:
            async with llm_span(model="child", service_name="child-service") as child:
                child.set_metadata("child_val", 1)
            parent.set_metadata("parent_val", 2)
        
        self.assertEqual(len(self.reporter.spans), 2)
        # Child reports first as it exits first
        child_span = self.reporter.spans[0]
        parent_span = self.reporter.spans[1]
        self.assertEqual(child_span["model"], "child")
        self.assertEqual(parent_span["model"], "parent")
        self.assertEqual(child_span["child_val"], 1)
        self.assertEqual(parent_span["parent_val"], 2)

    async def test_concurrent_spans(self):
        async def run_span(name: str, delay: float):
            async with llm_span(model=name, service_name="concurrent-test") as span:
                await asyncio.sleep(delay)
                span.set_metadata("done", True)

        await asyncio.gather(
            run_span("span-1", 0.02),
            run_span("span-2", 0.01),
            run_span("span-3", 0.03)
        )

        self.assertEqual(len(self.reporter.spans), 3)
        models = [s["model"] for s in self.reporter.spans]
        self.assertIn("span-1", models)
        self.assertIn("span-2", models)
        self.assertIn("span-3", models)

    def test_complex_metadata(self):
        complex_data = {
            "list": [1, 2, {"a": 3}],
            "dict": {"nested": "value", "deep": {"key": True}},
            "none": None
        }
        with llm_span(model="complex") as span:
            span.set_metadata("payload", complex_data)
        
    def test_reporter_failure(self):
        class FailingReporter:
            def report(self, span_data: Dict[str, Any]) -> None:
                raise RuntimeError("Reporter failed")
            async def report_async(self, span_data: Dict[str, Any]) -> None:
                raise RuntimeError("Reporter failed async")

        set_reporter(FailingReporter())
        
        # Currently, this WILL raise the exception to the caller.
        # This is the current behavior. If we want to change it to be "safe",
        # we would need to wrap it in try-except in the service.
        with self.assertRaises(RuntimeError):
            with llm_span(model="fail") as span:
                pass

if __name__ == "__main__":
    unittest.main()
