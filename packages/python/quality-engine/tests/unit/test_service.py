from __future__ import annotations

from features.score_composite.types import CompositeScoreInput
from features.score_composite.service import score_composite

class SpyAlertPublisher:
    def __init__(self) -> None:
        self.published_alerts: list[tuple[str, dict[str, str] | None]] = []

    def publish_alert(self, message: str, metadata: dict[str, str] | None = None) -> None:
        self.published_alerts.append((message, metadata))

def test_service_successful_score():
    publisher = SpyAlertPublisher()
    inp = CompositeScoreInput(
        trace_id="test_trace",
        span_id="test_span",
        coherence_score=0.9,
        faithfulness_score=0.8,
    )
    result = score_composite(inp, publisher)
    assert result.composite_score is not None
    assert result.composite_score > 0.0
    assert result.quality_skipped_reason is None
    assert len(publisher.published_alerts) == 0

def test_service_all_null_triggers_alert():
    publisher = SpyAlertPublisher()
    inp = CompositeScoreInput(
        trace_id="test_trace_null",
        span_id="test_span_null",
        coherence_score=None,
        faithfulness_score=None,
        toxicity_score=None,
        perplexity=None,
    )
    result = score_composite(inp, publisher)
    assert result.composite_score is None
    assert result.quality_skipped_reason == "all_scores_null"
    assert len(publisher.published_alerts) == 1
    msg, meta = publisher.published_alerts[0]
    assert "scoring pipeline is broken" in msg
    assert meta["trace_id"] == "test_trace_null"
    assert meta["span_id"] == "test_span_null"
