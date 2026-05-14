import unittest
import asyncio
import time
import uuid
from typing import Any, Dict, Generator, AsyncGenerator
from src.features.spans.decorator import llm_observe
from src.features.spans.globals import set_reporter, get_reporter, NoOpReporter

class MockReporter:
    def __init__(self):
        self.spans = []

    def report(self, span_data: Dict[str, Any]) -> None:
        self.spans.append(span_data)

    async def report_async(self, span_data: Dict[str, Any]) -> None:
        self.spans.append(span_data)

class TestDecoratorEdgeCases(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.reporter = MockReporter()
        set_reporter(self.reporter)

    def test_01_sync_success(self):
        @llm_observe(service="test", endpoint="sync")
        def func(x): return x
        self.assertEqual(func(1), 1)
        self.assertEqual(len(self.reporter.spans), 1)
        self.assertEqual(self.reporter.spans[0]["status"], "success")

    async def test_02_async_success(self):
        @llm_observe(service="test", endpoint="async")
        async def func(x): return x
        self.assertEqual(await func(1), 1)
        self.assertEqual(len(self.reporter.spans), 1)
        self.assertEqual(self.reporter.spans[0]["status"], "success")

    def test_03_sync_exception(self):
        @llm_observe(service="test", endpoint="sync-err")
        def func(): raise ValueError("fail")
        with self.assertRaises(ValueError):
            func()
        self.assertEqual(self.reporter.spans[0]["status"], "error")

    async def test_04_async_exception(self):
        @llm_observe(service="test", endpoint="async-err")
        async def func(): raise ValueError("fail")
        with self.assertRaises(ValueError):
            await func()
        self.assertEqual(self.reporter.spans[0]["status"], "error")

    def test_05_sync_method(self):
        class MyClass:
            @llm_observe(service="test", endpoint="method")
            def run(self, x): return x
        obj = MyClass()
        self.assertEqual(obj.run(10), 10)
        self.assertEqual(len(self.reporter.spans), 1)

    async def test_06_async_method(self):
        class MyClass:
            @llm_observe(service="test", endpoint="async-method")
            async def run(self, x): return x
        obj = MyClass()
        self.assertEqual(await obj.run(10), 10)
        self.assertEqual(len(self.reporter.spans), 1)

    def test_07_latency_measurement(self):
        @llm_observe(service="test", endpoint="latency")
        def slow(): time.sleep(0.05); return True
        slow()
        self.assertGreaterEqual(self.reporter.spans[0]["latency_ms_total"], 50)

    def test_08_no_reporter_crash_safety(self):
        set_reporter(NoOpReporter())
        @llm_observe(service="test", endpoint="noop")
        def func(): return True
        self.assertTrue(func())

    def test_09_reporter_dynamic_swap(self):
        @llm_observe(service="test", endpoint="swap")
        def func(): return True
        
        rep2 = MockReporter()
        set_reporter(rep2)
        func()
        self.assertEqual(len(rep2.spans), 1)
        self.assertEqual(len(self.reporter.spans), 0)

    async def test_10_concurrent_async_calls(self):
        @llm_observe(service="test", endpoint="concurrent")
        async def task(i): 
            await asyncio.sleep(0.01)
            return i
        
        results = await asyncio.gather(*(task(i) for i in range(5)))
        self.assertEqual(results, [0, 1, 2, 3, 4])
        self.assertEqual(len(self.reporter.spans), 5)

    def test_11_args_kwargs_preservation(self):
        @llm_observe(service="test", endpoint="params")
        def func(a, b, c=3): return a + b + c
        self.assertEqual(func(1, 2, c=10), 13)

    def test_12_nested_span_uniqueness(self):
        @llm_observe(service="test", endpoint="outer")
        def outer():
            @llm_observe(service="test", endpoint="inner")
            def inner(): return True
            return inner()
        
        outer()
        self.assertEqual(len(self.reporter.spans), 2)
        self.assertNotEqual(self.reporter.spans[0]["span_id"], self.reporter.spans[1]["span_id"])

    def test_13_uuid_format_validation(self):
        @llm_observe(service="test", endpoint="uuid")
        def func(): return True
        func()
        span_id = self.reporter.spans[0]["span_id"]
        # Should not raise if valid UUID
        uuid.UUID(span_id)

if __name__ == "__main__":
    unittest.main()
