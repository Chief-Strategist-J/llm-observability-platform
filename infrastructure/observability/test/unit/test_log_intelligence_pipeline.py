import unittest

from infrastructure.observability.server.log_intelligence_pipeline import (
    CountMinSketch,
    LogIntelligencePipeline,
    RawLogRecord,
)


class TestCountMinSketch(unittest.TestCase):
    def test_tracks_frequency(self):
        sketch = CountMinSketch(width=2000, depth=7)
        sketch.add("template-a")
        sketch.add("template-a", count=2)
        self.assertGreaterEqual(sketch.estimate("template-a"), 3)
        self.assertLess(sketch.epsilon, 0.002)
        self.assertLess(sketch.delta, 0.001)


class TestLogIntelligencePipeline(unittest.TestCase):
    def test_ingest_extracts_and_links_trace(self):
        pipeline = LogIntelligencePipeline()
        log = RawLogRecord(
            line_id="line-1",
            message="2026-04-27T10:00:00Z INFO service=checkout trace_id=trace-123 order 9001 failed",
        )

        parsed = pipeline.ingest(log)

        self.assertEqual(parsed.normalized_fields["level"], "INFO")
        self.assertEqual(parsed.normalized_fields["service"], "checkout")
        self.assertEqual(parsed.normalized_fields["trace_id"], "trace-123")
        self.assertEqual(len(parsed.embedding), 384)

        linked_lines = pipeline.trace_index.lookup("trace-123")
        self.assertEqual(linked_lines, ["line-1"])


if __name__ == "__main__":
    unittest.main()
