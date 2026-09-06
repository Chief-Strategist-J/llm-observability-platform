import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient

from src.api.rest.v1.app import app
from src.features.spans.tool_call_tracker import (
    track_tool_call,
    get_trace_total_cost,
    clear_tool_call_tracker
)
from src.features.minilm_embedding.index import (
    enrich_and_report_span,
    enrich_and_report_span_async
)
from src.features.spans.types import FinishReason
from src.features.spans.globals import get_reporter, set_reporter, NoOpReporter

def test_tracker_basic_functionality():
    clear_tool_call_tracker()
    trace_id = str(uuid.uuid4())
    span_id1 = str(uuid.uuid4())
    span_id2 = str(uuid.uuid4())

    assert get_trace_total_cost(trace_id) == 0

    assert track_tool_call(trace_id, span_id1, 100) == 100
    assert get_trace_total_cost(trace_id) == 100

    assert track_tool_call(trace_id, span_id1, 100) == 100
    assert get_trace_total_cost(trace_id) == 100

    assert track_tool_call(trace_id, span_id2, 150) == 250
    assert get_trace_total_cost(trace_id) == 250

    clear_tool_call_tracker()
    assert get_trace_total_cost(trace_id) == 0

def test_enrich_and_report_tool_calls():
    mock_reporter = MagicMock()
    set_reporter(mock_reporter)
    clear_tool_call_tracker()

    try:
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()

        span_data = {
            "span_id": span_id,
            "trace_id": trace_id,
            "schema_version": 1,
            "model": "gpt-4",
            "provider": "openai",
            "service_name": "test",
            "endpoint": "/test",
            "environment": "production",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "latency_ms_total": 500,
            "finish_reason": "tool_calls",
            "cost_usd_micro": 1500,
            "price_version": "2025-01-15",
            "token_count_method": "tiktoken",
            "timestamp_utc": now_str
        }

        enrich_and_report_span(span_data)

        reported_spans = [call[0][0] for call in mock_reporter.report_async.call_args_list]
        if not reported_spans:
            reported_spans = [call[0][0] for call in mock_reporter.report.call_args_list]

        assert len(reported_spans) >= 2

        original_span = None
        intermediate_span = None

        for s in reported_spans:
            if str(s.get("span_id")) == span_id:
                original_span = s
            elif str(s.get("parent_span_id")) == span_id:
                intermediate_span = s

        assert original_span is not None
        assert intermediate_span is not None
        assert intermediate_span["trace_id"] == trace_id
        assert intermediate_span["parent_span_id"] == span_id
        assert intermediate_span["finish_reason"] == FinishReason.STOP
        assert intermediate_span["cost_usd_micro"] == 0
        assert intermediate_span["prompt_tokens"] == 1
        assert get_trace_total_cost(trace_id) == 1500

    finally:
        set_reporter(NoOpReporter())

@pytest.mark.asyncio
async def test_enrich_and_report_tool_calls_async():
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    clear_tool_call_tracker()

    try:
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()

        span_data = {
            "span_id": span_id,
            "trace_id": trace_id,
            "schema_version": 1,
            "model": "gpt-4",
            "provider": "openai",
            "service_name": "test",
            "endpoint": "/test",
            "environment": "production",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "latency_ms_total": 500,
            "finish_reason": FinishReason.TOOL_CALLS,
            "cost_usd_micro": 1500,
            "price_version": "2025-01-15",
            "token_count_method": "tiktoken",
            "timestamp_utc": now_str
        }

        await enrich_and_report_span_async(span_data)

        reported_spans = [call[0][0] for call in mock_reporter.report_async.call_args_list]

        assert len(reported_spans) >= 2

        original_span = None
        intermediate_span = None

        for s in reported_spans:
            if str(s.get("span_id")) == span_id:
                original_span = s
            elif str(s.get("parent_span_id")) == span_id:
                intermediate_span = s

        assert original_span is not None
        assert intermediate_span is not None
        assert intermediate_span["trace_id"] == trace_id
        assert intermediate_span["parent_span_id"] == span_id
        assert intermediate_span["finish_reason"] == FinishReason.STOP
        assert intermediate_span["cost_usd_micro"] == 0
        assert intermediate_span["prompt_tokens"] == 1
        assert get_trace_total_cost(trace_id) == 1500

    finally:
        set_reporter(NoOpReporter())

def test_tool_call_api_endpoints():
    client = TestClient(app)
    res_clear = client.post("/v1/tool-call/clear")
    assert res_clear.status_code == 200
    assert res_clear.json() == {"success": True}

    trace_id = str(uuid.uuid4())
    span_id = str(uuid.uuid4())
    res_track = client.post("/v1/tool-call/track", json={
        "trace_id": trace_id,
        "span_id": span_id,
        "cost": 500
    })
    assert res_track.status_code == 200
    assert res_track.json() == {"total_cost": 500}

    res_track2 = client.post("/v1/tool-call/track", json={
        "trace_id": trace_id,
        "span_id": span_id,
        "cost": 500
    })
    assert res_track2.status_code == 200
    assert res_track2.json() == {"total_cost": 500}

    span_id2 = str(uuid.uuid4())
    res_track3 = client.post("/v1/tool-call/track", json={
        "trace_id": trace_id,
        "span_id": span_id2,
        "cost": 300
    })
    assert res_track3.status_code == 200
    assert res_track3.json() == {"total_cost": 800}
