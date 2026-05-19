import pytest
from unittest.mock import MagicMock
from features.metrics.service import MetricsService


MOCK_PRICES = [
    {
        "model": "gpt-4o",
        "provider": "openai",
        "input_price_per_1m": 5.00,
        "output_price_per_1m": 15.00,
        "version": "2025-01-15",
    },
    {
        "model": "gpt-3.5-turbo",
        "provider": "openai",
        "input_price_per_1m": 0.50,
        "output_price_per_1m": 1.50,
        "version": "2024-05-13",
    },
]


def _make_adapter():
    adapter = MagicMock()
    adapter.record_tokens = MagicMock()
    adapter.record_cost = MagicMock()
    adapter.record_latency = MagicMock()
    adapter.record_ttft = MagicMock()
    adapter.record_pii = MagicMock()
    adapter.record_injection = MagicMock()
    adapter.record_finish_reason = MagicMock()
    adapter.record_span = MagicMock()
    return adapter


def test_cost_computation_from_prices():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=MOCK_PRICES)
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "latency_ms_total": 200,
        "status": "success",
    }
    svc.record_span_telemetry(span)

    expected_cost = int((1000 * 5.00 + 500 * 15.00) / 1_000_000 * 1_000_000)
    assert span["cost_usd_micro"] == expected_cost
    assert span["price_version"] == "2025-01-15"


def test_cost_not_overwritten_when_already_set():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=MOCK_PRICES)
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "cost_usd_micro": 9999,
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "latency_ms_total": 200,
        "status": "success",
    }
    svc.record_span_telemetry(span)
    assert span["cost_usd_micro"] == 9999


def test_token_recording():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=MOCK_PRICES)
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "prompt_tokens": 100,
        "completion_tokens": 200,
        "latency_ms_total": 50,
        "status": "success",
    }
    svc.record_span_telemetry(span)
    calls = adapter.record_tokens.call_args_list
    assert len(calls) == 2
    assert calls[0][0][0] == 100
    assert calls[0][0][1]["token_type"] == "prompt"
    assert calls[1][0][0] == 200
    assert calls[1][0][1]["token_type"] == "completion"


def test_latency_recording():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=[])
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "latency_ms_total": 350,
        "status": "success",
    }
    svc.record_span_telemetry(span)
    adapter.record_latency.assert_called_once()
    assert adapter.record_latency.call_args[0][0] == 350


def test_ttft_recording():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=[])
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "latency_ms_total": 350,
        "latency_ms_ttft": 42,
        "status": "success",
    }
    svc.record_span_telemetry(span)
    adapter.record_ttft.assert_called_once()
    assert adapter.record_ttft.call_args[0][0] == 42


def test_pii_detection_recording():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=[])
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "pii_detected": True,
        "latency_ms_total": 100,
        "status": "success",
    }
    svc.record_span_telemetry(span)
    adapter.record_pii.assert_called_once_with({"service_name": "chat-api"})


def test_injection_attempt_recording():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=[])
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "injection_attempt": True,
        "latency_ms_total": 100,
        "status": "success",
    }
    svc.record_span_telemetry(span)
    adapter.record_injection.assert_called_once_with({"service_name": "chat-api"})


def test_finish_reason_recording():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=[])
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "finish_reason": "stop",
        "latency_ms_total": 100,
        "status": "success",
    }
    svc.record_span_telemetry(span)
    adapter.record_finish_reason.assert_called_once()
    labels = adapter.record_finish_reason.call_args[0][0]
    assert labels["finish_reason"] == "stop"
    assert labels["model"] == "gpt-4o"


def test_span_counter_with_retries():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=[])
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "latency_ms_total": 100,
        "status": "success",
        "retry_count": 3,
    }
    svc.record_span_telemetry(span)
    adapter.record_span.assert_called_once()
    labels = adapter.record_span.call_args[0][0]
    assert labels["has_retries"] == "true"
    assert labels["status"] == "success"


def test_span_counter_without_retries():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=[])
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "latency_ms_total": 100,
        "status": "error",
    }
    svc.record_span_telemetry(span)
    labels = adapter.record_span.call_args[0][0]
    assert labels["has_retries"] == "false"
    assert labels["status"] == "error"


def test_exception_does_not_propagate():
    adapter = MagicMock()
    adapter.record_span = MagicMock(side_effect=RuntimeError("boom"))
    svc = MetricsService(adapter, prices=[])
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "latency_ms_total": 100,
        "status": "success",
    }
    svc.record_span_telemetry(span)


def test_unknown_model_no_cost():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=MOCK_PRICES)
    span = {
        "model": "claude-3-opus",
        "provider": "anthropic",
        "service_name": "chat-api",
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "latency_ms_total": 200,
        "status": "success",
    }
    svc.record_span_telemetry(span)
    assert span.get("cost_usd_micro") is None
    adapter.record_cost.assert_not_called()


def test_no_tokens_skips_token_recording():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=[])
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "latency_ms_total": 100,
        "status": "success",
    }
    svc.record_span_telemetry(span)
    adapter.record_tokens.assert_not_called()
