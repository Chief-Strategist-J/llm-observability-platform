import uuid
from src import should_sample, llm_span
from src.features.spans.types import LLMSpan

def test_should_sample_determinism():
    span_id = uuid.uuid4()
    first = should_sample(span_id)
    second = should_sample(span_id)
    assert first == second

def test_should_sample_types():
    span_id = uuid.uuid4()
    res1 = should_sample(span_id)
    res2 = should_sample(str(span_id))
    res3 = should_sample(span_id.bytes)
    assert res1 == res2 == res3

def test_sampling_rate_distribution():
    sampled_count = 0
    total = 1000
    for _ in range(total):
        if should_sample(uuid.uuid4()):
            sampled_count += 1
    assert 0 <= sampled_count <= 50

def test_span_context_drops_sampled_fields():
    sampled_id = None
    unsampled_id = None
    while sampled_id is None or unsampled_id is None:
        u = uuid.uuid4()
        if should_sample(u):
            sampled_id = u
        else:
            unsampled_id = u

    from unittest.mock import patch
    with patch("src.features.manual_instrumentation.service.uuid.uuid4", return_value=sampled_id), \
         patch("src.features.minilm_embedding.index.enrich_and_report_span"):
        with llm_span(prompt="hello", prompt_hash="a"*64, prompt_embedding=[0.1]*384) as span:
            data = span._data
    assert data["is_sampled"] is True
    assert data["prompt_hash"] == "a"*64
    assert data["prompt_embedding"] == [0.1]*384

    with patch("src.features.manual_instrumentation.service.uuid.uuid4", return_value=unsampled_id), \
         patch("src.features.minilm_embedding.index.enrich_and_report_span"):
        with llm_span(prompt="hello", prompt_hash="a"*64, prompt_embedding=[0.1]*384) as span:
            data = span._data
    assert data["is_sampled"] is False
    assert data["prompt_hash"] is None
    assert data["prompt_embedding"] is None

def test_span_context_prevents_setting_sampled_fields():
    unsampled_id = None
    while unsampled_id is None:
        u = uuid.uuid4()
        if not should_sample(u):
            unsampled_id = u

    from unittest.mock import patch
    with patch("src.features.manual_instrumentation.service.uuid.uuid4", return_value=unsampled_id), \
         patch("src.features.minilm_embedding.index.enrich_and_report_span"):
        with llm_span(prompt="hello") as span:
            span.set_metadata("prompt_hash", "a"*64)
            span.set_metadata("prompt_embedding", [0.1]*384)
            data = span._data
    assert data.get("prompt_hash") is None
    assert data.get("prompt_embedding") is None

def test_llm_span_model_validator_sampled_fields():
    sampled_id = None
    unsampled_id = None
    while sampled_id is None or unsampled_id is None:
        u = uuid.uuid4()
        if should_sample(u):
            sampled_id = u
        else:
            unsampled_id = u

    from datetime import datetime, timezone
    from src.features.spans.types import Environment, FinishReason, TokenCountMethod

    base_data = {
        "trace_id": uuid.uuid4(),
        "schema_version": 1,
        "model": "gpt-4",
        "provider": "openai",
        "service_name": "test",
        "endpoint": "/v1/chat",
        "environment": Environment.DEV,
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "latency_ms_total": 100,
        "finish_reason": FinishReason.STOP,
        "cost_usd_micro": 0,
        "price_version": "v1",
        "token_count_method": TokenCountMethod.TIKTOKEN,
        "timestamp_utc": datetime.now(timezone.utc),
        "prompt_hash": "a"*64,
        "prompt_embedding": [0.1]*384,
    }

    sampled_data = {**base_data, "span_id": sampled_id, "is_sampled": True}
    span_sampled = LLMSpan(**sampled_data)
    assert span_sampled.prompt_hash == "a"*64
    assert span_sampled.prompt_embedding == [0.1]*384

    unsampled_data = {**base_data, "span_id": unsampled_id, "is_sampled": False}
    span_unsampled = LLMSpan(**unsampled_data)
    assert span_unsampled.prompt_hash is None
    assert span_unsampled.prompt_embedding is None
