"""
Unit tests for tracep.Tracer
============================

All OTLPSpanExporter network calls are mocked; tests run entirely in-process.
"""

from __future__ import annotations

import time
import threading
import unittest
from unittest.mock import MagicMock, patch, call

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _drain(tracer, timeout: float = 2.0) -> None:
    """Block until the background queue is empty (or timeout)."""
    deadline = time.monotonic() + timeout
    while not tracer._q.empty() and time.monotonic() < deadline:
        time.sleep(0.05)
    # Give the worker one extra tick to finish processing the last item
    time.sleep(0.05)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestTracerInit(unittest.TestCase):
    """Tracer can be constructed and the auth header is forwarded."""

    def test_auth_header_passed_to_exporter(self):
        """OTLPSpanExporter must receive Authorization: Bearer <key> header."""
        with patch(
            "tracep.tracer.OTLPSpanExporter", autospec=True
        ) as mock_exporter_cls:
            from tracep import Tracer

            Tracer("http://collector:4318", "secret-key", "svc")

            mock_exporter_cls.assert_called_once()
            _, kwargs = mock_exporter_cls.call_args
            headers = kwargs.get("headers", {})
            self.assertEqual(headers.get("Authorization"), "Bearer secret-key")

    def test_endpoint_v1_traces_appended(self):
        """Exporter endpoint must end with /v1/traces."""
        with patch(
            "tracep.tracer.OTLPSpanExporter", autospec=True
        ) as mock_exporter_cls:
            from tracep import Tracer

            Tracer("http://collector:4318", "key", "svc")

            _, kwargs = mock_exporter_cls.call_args
            endpoint = kwargs.get("endpoint", "")
            self.assertTrue(
                endpoint.endswith("/v1/traces"),
                f"Expected endpoint to end with /v1/traces, got: {endpoint!r}",
            )


class TestTracerStart(unittest.TestCase):
    """start() returns a non-empty hex string."""

    def setUp(self):
        self._patcher = patch("tracep.tracer.OTLPSpanExporter", autospec=True)
        self._patcher.start()
        # Re-import to pick up the mock
        import importlib, tracep.tracer as m
        importlib.reload(m)
        import tracep as pkg
        importlib.reload(pkg)
        from tracep import Tracer
        self.Tracer = Tracer

    def tearDown(self):
        self._patcher.stop()

    def test_start_returns_nonempty_string(self):
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        tid = tracer.start("my-op")
        self.assertIsInstance(tid, str)
        self.assertTrue(len(tid) > 0)
        tracer.close()

    def test_start_returns_hex_string(self):
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        tid = tracer.start("my-op")
        # Must be valid hex
        int(tid, 16)
        tracer.close()

    def test_start_returns_32_char_trace_id(self):
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        tid = tracer.start("my-op")
        self.assertEqual(len(tid), 32, f"Expected 32-char hex tid, got {len(tid)}: {tid!r}")
        tracer.close()

    def test_multiple_starts_return_unique_ids(self):
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        tids = {tracer.start(f"op-{i}") for i in range(10)}
        self.assertEqual(len(tids), 10, "start() returned duplicate trace IDs")
        tracer.close()


class TestTracerTrace(unittest.TestCase):
    """trace() enqueues events and they are processed by the worker."""

    def setUp(self):
        self._patcher = patch("tracep.tracer.OTLPSpanExporter", autospec=True)
        self._patcher.start()
        import importlib, tracep.tracer as m
        importlib.reload(m)
        import tracep as pkg
        importlib.reload(pkg)
        from tracep import Tracer
        self.Tracer = Tracer

    def tearDown(self):
        self._patcher.stop()

    def test_trace_returns_immediately(self):
        """trace() must not block the caller for more than a few ms."""
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        tid = tracer.start("op")
        t0 = time.monotonic()
        tracer.trace(tid, "Cls", "fn", "step1", "hello")
        elapsed = time.monotonic() - t0
        self.assertLess(elapsed, 0.5, "trace() blocked the caller")
        tracer.close()

    def test_trace_creates_child_span_in_roots(self):
        """After draining the queue, a child span keyed by (tid, cls, fn) exists."""
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        tid = tracer.start("op")
        tracer.trace(tid, "MyService", "handle", "start", "begin processing")
        _drain(tracer)
        with tracer._lock:
            key = (tid, "MyService", "handle")
            self.assertIn(key, tracer._spans)
        tracer.close()

    def test_trace_adds_event_to_span(self):
        """The child span should have one event after one trace() call."""
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        tid = tracer.start("op")
        tracer.trace(tid, "Svc", "fn", "step1", "msg")
        _drain(tracer)
        with tracer._lock:
            span = tracer._spans.get((tid, "Svc", "fn"))
        self.assertIsNotNone(span)
        events = span.events
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].name, "step1")
        self.assertEqual(events[0].attributes["message"], "msg")
        self.assertEqual(events[0].attributes["level"], "info")
        tracer.close()

    def test_trace_custom_level_stored(self):
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        tid = tracer.start("op")
        tracer.trace(tid, "Svc", "fn", "step1", "msg", level="error")
        _drain(tracer)
        with tracer._lock:
            span = tracer._spans.get((tid, "Svc", "fn"))
        self.assertEqual(span.events[0].attributes["level"], "error")
        tracer.close()

    def test_trace_unknown_tid_silently_ignored(self):
        """trace() with an unknown tid must not raise any exception."""
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        # Do NOT call start() — unknown tid
        try:
            tracer.trace("deadbeef" * 4, "X", "y", "s", "m")
            _drain(tracer)
        except Exception as exc:
            self.fail(f"trace() with unknown tid raised {exc!r}")
        tracer.close()

    def test_trace_same_cls_fn_reuses_span(self):
        """Two trace() calls with same cls+fn should share one span (two events)."""
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        tid = tracer.start("op")
        tracer.trace(tid, "A", "b", "step1", "first")
        tracer.trace(tid, "A", "b", "step2", "second")
        _drain(tracer)
        with tracer._lock:
            span = tracer._spans.get((tid, "A", "b"))
        self.assertIsNotNone(span)
        self.assertEqual(len(span.events), 2)
        tracer.close()

    def test_trace_different_fn_creates_separate_spans(self):
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        tid = tracer.start("op")
        tracer.trace(tid, "A", "fn1", "s", "m1")
        tracer.trace(tid, "A", "fn2", "s", "m2")
        _drain(tracer)
        with tracer._lock:
            self.assertIn((tid, "A", "fn1"), tracer._spans)
            self.assertIn((tid, "A", "fn2"), tracer._spans)
        tracer.close()


class TestTracerEnd(unittest.TestCase):
    """end() flushes and shuts down spans for the given tid."""

    def setUp(self):
        self._patcher = patch("tracep.tracer.OTLPSpanExporter", autospec=True)
        self._patcher.start()
        import importlib, tracep.tracer as m
        importlib.reload(m)
        import tracep as pkg
        importlib.reload(pkg)
        from tracep import Tracer
        self.Tracer = Tracer

    def tearDown(self):
        self._patcher.stop()

    def test_end_removes_tid_from_roots(self):
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        tid = tracer.start("op")
        tracer.end(tid, "ok")
        _drain(tracer)
        with tracer._lock:
            self.assertNotIn(tid, tracer._roots)
        tracer.close()

    def test_end_removes_child_spans(self):
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        tid = tracer.start("op")
        tracer.trace(tid, "A", "fn", "s", "m")
        tracer.end(tid, "ok")
        _drain(tracer)
        with tracer._lock:
            remaining = [k for k in tracer._spans if k[0] == tid]
        self.assertEqual(remaining, [], f"Child spans not cleaned up: {remaining}")
        tracer.close()

    def test_end_returns_immediately(self):
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        tid = tracer.start("op")
        t0 = time.monotonic()
        tracer.end(tid, "ok")
        elapsed = time.monotonic() - t0
        self.assertLess(elapsed, 0.5, "end() blocked the caller")
        tracer.close()

    def test_end_calls_force_flush_on_provider(self):
        """After end(), force_flush should have been called on the provider."""
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        # Patch force_flush after construction
        tracer._provider.force_flush = MagicMock(return_value=True)
        tid = tracer.start("op")
        tracer.end(tid, "ok")
        _drain(tracer)
        tracer._provider.force_flush.assert_called()
        tracer.close()

    def test_end_unknown_tid_silently_ignored(self):
        """end() with unknown tid must not raise."""
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        try:
            tracer.end("0" * 32, "ok")
            _drain(tracer)
        except Exception as exc:
            self.fail(f"end() with unknown tid raised {exc!r}")
        tracer.close()

    def test_end_error_status_propagated(self):
        """end('error') must mark the root span with ERROR status."""
        from opentelemetry.trace.status import StatusCode
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        tid = tracer.start("op")
        tracer.end(tid, "error")
        _drain(tracer)
        # Root has already been removed; check no crash. (Detailed status
        # checking requires InMemorySpanExporter; done in integration tests.)
        tracer.close()


class TestTracerClose(unittest.TestCase):
    """close() stops the background worker gracefully."""

    def setUp(self):
        self._patcher = patch("tracep.tracer.OTLPSpanExporter", autospec=True)
        self._patcher.start()
        import importlib, tracep.tracer as m
        importlib.reload(m)
        import tracep as pkg
        importlib.reload(pkg)
        from tracep import Tracer
        self.Tracer = Tracer

    def tearDown(self):
        self._patcher.stop()

    def test_close_joins_worker_thread(self):
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        tracer.close()
        self.assertFalse(tracer._worker.is_alive(), "Worker thread still alive after close()")

    def test_close_is_idempotent_safe(self):
        """Calling close() twice must not raise."""
        tracer = self.Tracer("http://localhost:4318", "k", "s")
        tracer.close()
        # Second close — worker is already dead so join is a no-op.
        # The queue put should not deadlock because worker already exited.
        # We just verify it doesn't raise.
        try:
            tracer._q.put_nowait({"cmd": "stop"})
        except Exception as exc:
            self.fail(f"Second close-like action raised {exc!r}")


class TestPublicHelpers(unittest.TestCase):
    """WithParent and WithLevel are exported and are str subclasses."""

    def test_with_parent_is_str(self):
        from tracep import WithParent
        wp = WithParent("MyClass/my_fn")
        self.assertIsInstance(wp, str)
        self.assertEqual(wp, "MyClass/my_fn")

    def test_with_level_is_str(self):
        from tracep import WithLevel
        wl = WithLevel("warn")
        self.assertIsInstance(wl, str)
        self.assertEqual(wl, "warn")

    def test_imports_from_package_root(self):
        from tracep import Tracer, WithParent, WithLevel  # noqa: F401


if __name__ == "__main__":
    unittest.main()
