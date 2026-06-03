import pytest
from unittest.mock import MagicMock
from src.features.metrics.registry import (
    SAFETY_METRICS_REGISTRY,
    MetricType,
    MetricEvaluator,
    MetricDefinition,
    _extract_toxicity_detected,
    _extract_toxicity_score,
)
from src.features.metrics.service import MetricsService


def _make_adapter_with_metric():
    adapter = MagicMock()
    adapter.record_tokens = MagicMock()
    adapter.record_cost = MagicMock()
    adapter.record_latency = MagicMock()
    adapter.record_ttft = MagicMock()
    adapter.record_pii = MagicMock()
    adapter.record_injection = MagicMock()
    adapter.record_finish_reason = MagicMock()
    adapter.record_span = MagicMock()
    adapter.record_metric = MagicMock()
    return adapter


class TestRegistryDefinitions:
    def test_registry_is_non_empty_tuple(self):
        assert isinstance(SAFETY_METRICS_REGISTRY, tuple)
        assert len(SAFETY_METRICS_REGISTRY) >= 2

    def test_all_evaluators_have_metric_definition(self):
        for ev in SAFETY_METRICS_REGISTRY:
            assert isinstance(ev, MetricEvaluator)
            assert isinstance(ev.metric, MetricDefinition)
            assert ev.metric.name
            assert ev.metric.metric_type in (MetricType.COUNTER, MetricType.HISTOGRAM)
            assert ev.metric.description
            assert ev.metric.unit

    def test_all_evaluators_have_callable_extract_fn(self):
        for ev in SAFETY_METRICS_REGISTRY:
            assert callable(ev.extract_fn)

    def test_metric_names_are_unique(self):
        names = [ev.metric.name for ev in SAFETY_METRICS_REGISTRY]
        assert len(names) == len(set(names))


class TestToxicityDetectedExtractor:
    def test_returns_none_when_no_toxicity(self):
        span = {"service_name": "svc"}
        assert _extract_toxicity_detected(span) is None

    def test_returns_none_when_score_below_threshold(self):
        span = {"service_name": "svc", "toxicity_score": 0.49}
        assert _extract_toxicity_detected(span) is None

    def test_triggers_on_score_above_threshold(self):
        span = {"service_name": "svc", "toxicity_score": 0.51}
        result = _extract_toxicity_detected(span)
        assert result is not None
        value, labels = result
        assert value == 1
        assert labels["service_name"] == "svc"

    def test_triggers_on_score_exactly_at_boundary(self):
        span = {"service_name": "svc", "toxicity_score": 0.50}
        assert _extract_toxicity_detected(span) is None

    def test_triggers_on_toxicity_detected_flag(self):
        span = {"service_name": "svc", "toxicity_detected": True}
        result = _extract_toxicity_detected(span)
        assert result is not None
        assert result[0] == 1

    def test_defaults_unknown_service_name(self):
        span = {"toxicity_score": 0.9}
        result = _extract_toxicity_detected(span)
        assert result is not None
        assert result[1]["service_name"] == "unknown"


class TestToxicityScoreExtractor:
    def test_returns_none_when_no_score(self):
        span = {"service_name": "svc"}
        assert _extract_toxicity_score(span) is None

    def test_returns_score_and_base_labels(self):
        span = {
            "service_name": "svc",
            "model": "gpt-4o",
            "provider": "openai",
            "toxicity_score": 0.73,
        }
        result = _extract_toxicity_score(span)
        assert result is not None
        value, labels = result
        assert abs(value - 0.73) < 1e-9
        assert labels["service_name"] == "svc"
        assert labels["model"] == "gpt-4o"
        assert labels["provider"] == "openai"

    def test_returns_zero_score(self):
        span = {"toxicity_score": 0.0}
        result = _extract_toxicity_score(span)
        assert result is not None
        assert result[0] == 0.0


class TestServiceRegistryDispatch:
    def test_record_metric_called_for_toxic_span(self):
        adapter = _make_adapter_with_metric()
        svc = MetricsService(adapter, prices=[])
        span = {
            "model": "gpt-4o",
            "provider": "openai",
            "service_name": "chat-api",
            "toxicity_score": 0.85,
            "latency_ms_total": 100,
            "status": "success",
        }
        svc.record_span_telemetry(span)
        calls = {c.args[0] for c in adapter.record_metric.call_args_list}
        assert "llm_toxicity_detected_total" in calls
        assert "llm_toxicity_score" in calls

    def test_record_metric_not_called_for_safe_span(self):
        adapter = _make_adapter_with_metric()
        svc = MetricsService(adapter, prices=[])
        span = {
            "model": "gpt-4o",
            "provider": "openai",
            "service_name": "chat-api",
            "toxicity_score": 0.1,
            "latency_ms_total": 100,
            "status": "success",
        }
        svc.record_span_telemetry(span)
        names = [c.args[0] for c in adapter.record_metric.call_args_list]
        assert "llm_toxicity_detected_total" not in names
        assert "llm_toxicity_score" in names

    def test_existing_tests_unaffected_when_adapter_lacks_record_metric(self):
        adapter = MagicMock(spec=["record_tokens", "record_cost", "record_latency",
                                   "record_ttft", "record_pii", "record_injection",
                                   "record_finish_reason", "record_span"])
        svc = MetricsService(adapter, prices=[])
        span = {
            "model": "gpt-4o",
            "provider": "openai",
            "service_name": "chat-api",
            "latency_ms_total": 100,
            "status": "success",
        }
        svc.record_span_telemetry(span)
        adapter.record_span.assert_called_once()
