import uuid
import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError
from features.spans.types import LLMSpan, FinishReason, TokenCountMethod, Environment

def get_valid_span_data():
    return {
        "span_id": uuid.uuid4(),
        "trace_id": uuid.uuid4(),
        "schema_version": 1,
        "model": "gpt-4o",
        "provider": "openai",
        "service_name": "test-service",
        "endpoint": "/api/test",
        "environment": Environment.PRODUCTION,
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "latency_ms_total": 500,
        "finish_reason": FinishReason.STOP,
        "cost_usd_micro": 1500,
        "price_version": "2025-01-15",
        "token_count_method": TokenCountMethod.TIKTOKEN,
        "is_sampled": False,
        "retry_count": 0,
        "pii_detected": False,
        "injection_attempt": False,
        "timestamp_utc": datetime.now(timezone.utc)
    }

def test_valid_span_success():
    data = get_valid_span_data()
    span = LLMSpan(**data)
    assert span.span_id == data["span_id"]
    assert len(span.span_warnings) == 0

def test_v02_prompt_tokens_le_zero():
    data = get_valid_span_data()
    data["prompt_tokens"] = 0
    with pytest.raises(ValidationError) as excinfo:
        LLMSpan(**data)
    assert "prompt_tokens" in str(excinfo.value)

def test_v03_latency_ms_total_le_zero():
    data = get_valid_span_data()
    data["latency_ms_total"] = 0
    with pytest.raises(ValidationError) as excinfo:
        LLMSpan(**data)
    assert "latency_ms_total" in str(excinfo.value)

def test_v09_timestamp_too_far_future():
    data = get_valid_span_data()
    data["timestamp_utc"] = datetime.now(timezone.utc) + timedelta(seconds=120)
    with pytest.raises(ValidationError) as excinfo:
        LLMSpan(**data)
    assert "RULE-V-09" in str(excinfo.value)

def test_v10_timestamp_too_old():
    data = get_valid_span_data()
    data["timestamp_utc"] = datetime.now(timezone.utc) - timedelta(days=8)
    with pytest.raises(ValidationError) as excinfo:
        LLMSpan(**data)
    assert "RULE-V-10" in str(excinfo.value)

def test_w01_estimated_token_method():
    data = get_valid_span_data()
    data["token_count_method"] = TokenCountMethod.ESTIMATED
    span = LLMSpan(**data)
    assert any("RULE-W-01" in w for w in span.span_warnings)

def test_w03_ttft_gt_total():
    data = get_valid_span_data()
    data["latency_ms_total"] = 500
    data["latency_ms_ttft"] = 600
    span = LLMSpan(**data)
    assert any("RULE-W-03" in w for w in span.span_warnings)
    assert span.latency_ms_ttft is None

def test_pii_detected_nullifies_sampled_fields():
    data = get_valid_span_data()
    data["pii_detected"] = True
    data["prompt_hash"] = "some-hash"
    data["prompt_embedding"] = [0.1] * 384
    span = LLMSpan(**data)
    assert span.prompt_hash is None
    assert span.prompt_embedding is None
