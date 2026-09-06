import unittest
import asyncio
from typing import Any, Dict
from src.features.spans.decorator import llm_observe
from src.features.spans.globals import set_reporter

class MockReporter:
    def __init__(self):
        self.spans = []

    def report(self, span_data: Dict[str, Any]) -> None:
        self.spans.append(span_data)

    async def report_async(self, span_data: Dict[str, Any]) -> None:
        self.spans.append(span_data)

class TestDecorator(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.reporter = MockReporter()
        set_reporter(self.reporter)

    def test_sync_observation(self):
        @llm_observe(service="test-service", endpoint="/test-sync")
        def sample_func(x):
            return x * 2
        
        result = sample_func(5)
        self.assertEqual(result, 10)
        self.assertEqual(len(self.reporter.spans), 1)
        
        span = self.reporter.spans[0]
        self.assertEqual(span["service_name"], "test-service")
        self.assertEqual(span["endpoint"], "/test-sync")
        self.assertIn("span_id", span)
        self.assertIn("latency_ms_total", span)

    async def test_async_observation(self):
        @llm_observe(service="test-service", endpoint="/test-async")
        async def sample_async_func(x):
            await asyncio.sleep(0.01)
            return x + 2
        
        result = await sample_async_func(5)
        self.assertEqual(result, 7)
        self.assertEqual(len(self.reporter.spans), 1)
        
        span = self.reporter.spans[0]
        self.assertEqual(span["service_name"], "test-service")
        self.assertEqual(span["endpoint"], "/test-async")
        self.assertGreaterEqual(span["latency_ms_total"], 10)

if __name__ == "__main__":
    unittest.main()
