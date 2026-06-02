from __future__ import annotations

from features.score_composite.types import CompositeScoreInput
from features.score_composite.service import score_composite

class SpyAlertPublisher:
    def __init__(self) -> None:
        self.published_alerts: list[tuple[str, dict[str, str] | None]] = []

    def publish_alert(self, message: str, metadata: dict[str, str] | None = None) -> None:
        self.published_alerts.append((message, metadata))

class MockScorerClient:
    def __init__(self) -> None:
        self.called_coherence = False
        self.called_faithfulness = False
        self.called_toxicity = False
        self.called_perplexity = False

    def get_coherence_score(
        self,
        trace_id: str,
        span_id: str,
        prompt_type: str | None,
        pii_detected: bool | None,
        prompt_embedding: list[float] | None,
        response_embedding: list[float] | None,
    ) -> float | None:
        self.called_coherence = True
        return 0.7

    def get_faithfulness_score(
        self,
        trace_id: str,
        span_id: str,
        response_text: str | None,
        completion_tokens: int | None,
        rag_context: str | None,
        finish_reason: str | None,
    ) -> float | None:
        self.called_faithfulness = True
        return 0.8

    def get_toxicity_score(
        self,
        trace_id: str,
        span_id: str,
        response_text: str | None,
    ) -> float | None:
        self.called_toxicity = True
        return 0.1

    def get_perplexity_value(
        self,
        trace_id: str,
        span_id: str,
        response_text: str | None,
        completion_tokens: int | None,
        prompt_type: str | None,
        token_logprobs: list[float] | None,
        finish_reason: str | None,
    ) -> float | None:
        self.called_perplexity = True
        return 1.5

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

def test_service_queries_scorer_client_when_scores_are_none():
    publisher = SpyAlertPublisher()
    client = MockScorerClient()
    inp = CompositeScoreInput(
        trace_id="test_trace_raw",
        span_id="test_span_raw",
        coherence_score=None,
        faithfulness_score=None,
        toxicity_score=None,
        perplexity=None,
        prompt_type="chat",
        response_text="some response",
        completion_tokens=10,
    )
    result = score_composite(inp, publisher, client)
    assert client.called_coherence
    assert client.called_faithfulness
    assert client.called_toxicity
    assert client.called_perplexity
    assert result.composite_score is not None
    assert result.quality_skipped_reason is None
