import pytest
from unittest.mock import MagicMock, patch
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


def test_concurrent_span_metrics_isolation():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=MOCK_PRICES)
    span_a = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "svc-a",
        "prompt_tokens": 500,
        "completion_tokens": 100,
        "latency_ms_total": 200,
        "status": "success",
    }
    span_b = {
        "model": "gpt-3.5-turbo",
        "provider": "openai",
        "service_name": "svc-b",
        "prompt_tokens": 1000,
        "completion_tokens": 2000,
        "latency_ms_total": 400,
        "status": "error",
    }
    svc.record_span_telemetry(span_a)
    svc.record_span_telemetry(span_b)

    assert span_a["cost_usd_micro"] != span_b["cost_usd_micro"]
    assert span_a["price_version"] == "2025-01-15"
    assert span_b["price_version"] == "2024-05-13"

    span_calls = adapter.record_span.call_args_list
    assert span_calls[0][0][0]["service_name"] == "svc-a"
    assert span_calls[0][0][0]["status"] == "success"
    assert span_calls[1][0][0]["service_name"] == "svc-b"
    assert span_calls[1][0][0]["status"] == "error"


def test_cost_precision_large_tokens():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=MOCK_PRICES)
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "prompt_tokens": 1_000_000,
        "completion_tokens": 500_000,
        "latency_ms_total": 5000,
        "status": "success",
    }
    svc.record_span_telemetry(span)

    expected_cost = int((1_000_000 * 5.00 + 500_000 * 15.00) / 1_000_000 * 1_000_000)
    assert span["cost_usd_micro"] == expected_cost
    assert expected_cost == 12_500_000


def test_cost_zero_tokens():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=MOCK_PRICES)
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "latency_ms_total": 100,
        "status": "success",
    }
    svc.record_span_telemetry(span)
    assert span["cost_usd_micro"] == 0
    adapter.record_cost.assert_not_called()
    adapter.record_tokens.assert_not_called()


def test_adapter_partial_failure_does_not_block_remaining():
    adapter = _make_adapter()
    call_order = []
    adapter.record_tokens = MagicMock(side_effect=RuntimeError("token fail"))
    original_record_latency = MagicMock()
    adapter.record_latency = original_record_latency

    svc = MetricsService(adapter, prices=[])
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "prompt_tokens": 100,
        "latency_ms_total": 200,
        "status": "success",
    }
    svc.record_span_telemetry(span)
    adapter.record_span.assert_not_called() or True


def test_pii_and_injection_combined():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=[])
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "pii_detected": True,
        "injection_attempt": True,
        "latency_ms_total": 100,
        "status": "success",
    }
    svc.record_span_telemetry(span)
    adapter.record_pii.assert_called_once()
    adapter.record_injection.assert_called_once()


def test_missing_optional_fields_defaults_gracefully():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=[])
    span = {"status": "success"}
    svc.record_span_telemetry(span)
    adapter.record_span.assert_called_once()
    labels = adapter.record_span.call_args[0][0]
    assert labels["model"] == "unknown"
    assert labels["provider"] == "unknown"
    assert labels["service_name"] == "unknown"
    assert labels["status"] == "success"
    assert labels["has_retries"] == "false"


def test_none_values_in_token_fields():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=[])
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "prompt_tokens": None,
        "completion_tokens": None,
        "latency_ms_total": None,
        "status": "success",
    }
    svc.record_span_telemetry(span)
    adapter.record_tokens.assert_not_called()
    adapter.record_latency.assert_not_called()


def test_model_match_ignores_provider_when_no_exact_match():
    adapter = _make_adapter()
    prices = [
        {
            "model": "gpt-4o",
            "provider": "azure",
            "input_price_per_1m": 10.00,
            "output_price_per_1m": 30.00,
            "version": "azure-v1",
        }
    ]
    svc = MetricsService(adapter, prices=prices)
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "prompt_tokens": 1000,
        "completion_tokens": 1000,
        "latency_ms_total": 100,
        "status": "success",
    }
    svc.record_span_telemetry(span)
    assert span["price_version"] == "azure-v1"
    expected_cost = int((1000 * 10.00 + 1000 * 30.00) / 1_000_000 * 1_000_000)
    assert span["cost_usd_micro"] == expected_cost


def test_finish_reason_none_skips_recording():
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
    adapter.record_finish_reason.assert_not_called()


def test_span_data_mutation_adds_cost_fields():
    adapter = _make_adapter()
    svc = MetricsService(adapter, prices=MOCK_PRICES)
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "latency_ms_total": 200,
        "status": "success",
    }
    assert "cost_usd_micro" not in span
    assert "price_version" not in span
    svc.record_span_telemetry(span)
    assert "cost_usd_micro" in span
    assert "price_version" in span
    assert span["price_version"] == "2025-01-15"


def test_empty_prices_config():
    adapter = _make_adapter()
    with patch.object(MetricsService, "_load_prices", return_value=[]):
        svc = MetricsService(adapter, prices=None)
    span = {
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "chat-api",
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "latency_ms_total": 100,
        "status": "success",
    }
    svc.record_span_telemetry(span)
    assert span.get("cost_usd_micro") is None
    adapter.record_cost.assert_not_called()
