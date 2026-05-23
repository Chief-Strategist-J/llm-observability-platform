import uuid
import pytest
import asyncio
import os
import threading
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from src import set_reporter
from src.features.spans.globals import NoOpReporter
from src.features.spans.fallback_tracker import track_fallback, clear_fallback_tracker
from src.features.minilm_embedding.index import enrich_and_report_span, enrich_and_report_span_async
from src.api.rest.v1.app import app

_REAL_THREAD = threading.Thread

@pytest.fixture(autouse=True)
def mock_sync_thread():
    class SyncThread:
        def __init__(self, *args, **kwargs):
            self.target = kwargs.get("target")
            self.args = kwargs.get("args", ())
            self.kwargs = kwargs.get("kwargs", {})
            self._is_sync_target = (self.target and self.target.__name__ == "_sync_enrich_and_report")
            if not self._is_sync_target:
                self._real_thread = _REAL_THREAD(*args, **kwargs)
        def start(self):
            if self._is_sync_target:
                if self.target:
                    self.target(*self.args, **self.kwargs)
            else:
                self._real_thread.start()
    with patch("threading.Thread", SyncThread):
        yield

@pytest.fixture(autouse=True)
def clean_tracker():
    clear_fallback_tracker()
    yield
    clear_fallback_tracker()

def test_tracker_basic_functionality():
    trace_id = str(uuid.uuid4())
    r1, m1 = track_fallback(trace_id, "gpt-4")
    assert r1 == 0
    assert m1 == ["gpt-4"]

    r2, m2 = track_fallback(trace_id, "claude-3")
    assert r2 == 1
    assert m2 == ["gpt-4", "claude-3"]

    r3, m3 = track_fallback(trace_id, "llama-3")
    assert r3 == 2
    assert m3 == ["gpt-4", "claude-3", "llama-3"]

def test_tracker_empty_values():
    r1, m1 = track_fallback(None, "gpt-4")
    assert r1 == 0
    assert m1 == ["gpt-4"]

    r2, m2 = track_fallback("", "gpt-4")
    assert r2 == 0
    assert m2 == ["gpt-4"]

def test_enrich_and_report_fallback():
    mock_reporter = MagicMock()
    set_reporter(mock_reporter)
    try:
        trace_id = uuid.uuid4()
        now_str = datetime.now(timezone.utc).isoformat()
        span1 = {
            "span_id": str(uuid.uuid4()),
            "trace_id": trace_id,
            "model": "gpt-4",
            "provider": "openai",
            "service_name": "test",
            "endpoint": "/test",
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "latency_ms_total": 100,
            "finish_reason": "stop",
            "cost_usd_micro": 10,
            "price_version": "v1",
            "token_count_method": "tiktoken",
            "timestamp_utc": now_str
        }
        span2 = {
            "span_id": str(uuid.uuid4()),
            "trace_id": trace_id,
            "model": "claude-3",
            "provider": "anthropic",
            "service_name": "test",
            "endpoint": "/test",
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "latency_ms_total": 100,
            "finish_reason": "stop",
            "cost_usd_micro": 10,
            "price_version": "v1",
            "token_count_method": "tiktoken",
            "timestamp_utc": now_str
        }

        enrich_and_report_span(span1)
        assert mock_reporter.report.called
        reported1 = mock_reporter.report.call_args[0][0]
        assert reported1["retry_count"] == 0
        assert reported1["attempted_models"] == ["gpt-4"]

        mock_reporter.reset_mock()
        enrich_and_report_span(span2)
        assert mock_reporter.report.called
        reported2 = mock_reporter.report.call_args[0][0]
        assert reported2["retry_count"] == 1
        assert reported2["attempted_models"] == ["gpt-4", "claude-3"]
    finally:
        set_reporter(NoOpReporter())

@pytest.mark.asyncio
async def test_enrich_and_report_fallback_async():
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    try:
        trace_id = uuid.uuid4()
        now_str = datetime.now(timezone.utc).isoformat()
        span1 = {
            "span_id": str(uuid.uuid4()),
            "trace_id": trace_id,
            "model": "gpt-4",
            "provider": "openai",
            "service_name": "test",
            "endpoint": "/test",
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "latency_ms_total": 100,
            "finish_reason": "stop",
            "cost_usd_micro": 10,
            "price_version": "v1",
            "token_count_method": "tiktoken",
            "timestamp_utc": now_str
        }
        span2 = {
            "span_id": str(uuid.uuid4()),
            "trace_id": trace_id,
            "model": "claude-3",
            "provider": "anthropic",
            "service_name": "test",
            "endpoint": "/test",
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "latency_ms_total": 100,
            "finish_reason": "stop",
            "cost_usd_micro": 10,
            "price_version": "v1",
            "token_count_method": "tiktoken",
            "timestamp_utc": now_str
        }

        await enrich_and_report_span_async(span1)
        assert mock_reporter.report_async.called
        reported1 = mock_reporter.report_async.call_args[0][0]
        assert reported1["retry_count"] == 0
        assert reported1["attempted_models"] == ["gpt-4"]

        mock_reporter.reset_mock()
        await enrich_and_report_span_async(span2)
        assert mock_reporter.report_async.called
        reported2 = mock_reporter.report_async.call_args[0][0]
        assert reported2["retry_count"] == 1
        assert reported2["attempted_models"] == ["gpt-4", "claude-3"]
    finally:
        set_reporter(NoOpReporter())

def test_api_spans_fallback():
    mock_reporter = MagicMock()
    set_reporter(mock_reporter)
    client = TestClient(app)
    try:
        trace_id = str(uuid.uuid4())
        span_id1 = str(uuid.uuid4())
        span_id2 = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()
        
        payload1 = {
            "span_id": span_id1,
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
            "finish_reason": "stop",
            "cost_usd_micro": 1500,
            "price_version": "2025-01-15",
            "token_count_method": "tiktoken",
            "timestamp_utc": now_str
        }
        payload2 = {
            "span_id": span_id2,
            "trace_id": trace_id,
            "schema_version": 1,
            "model": "claude-3",
            "provider": "anthropic",
            "service_name": "test",
            "endpoint": "/test",
            "environment": "production",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "latency_ms_total": 500,
            "finish_reason": "stop",
            "cost_usd_micro": 1500,
            "price_version": "2025-01-15",
            "token_count_method": "tiktoken",
            "timestamp_utc": now_str
        }

        res1 = client.post("/v1/spans", json=payload1)
        assert res1.status_code == 202
        data1 = res1.json()
        assert not any("RULE-W-05" in w for w in data1.get("span_warnings", []))
        reported1 = None
        for call in mock_reporter.report.call_args_list:
            if call[0][0].get("span_id") == span_id1 or str(call[0][0].get("span_id")) == span_id1:
                reported1 = call[0][0]
                break
        assert reported1 is not None
        assert reported1["retry_count"] == 0
        assert reported1["attempted_models"] == ["gpt-4"]

        mock_reporter.reset_mock()
        res2 = client.post("/v1/spans", json=payload2)
        assert res2.status_code == 202
        data2 = res2.json()
        assert any("RULE-W-05" in w for w in data2.get("span_warnings", []))
        reported2 = None
        for call in mock_reporter.report.call_args_list:
            if call[0][0].get("span_id") == span_id2 or str(call[0][0].get("span_id")) == span_id2:
                reported2 = call[0][0]
                break
        assert reported2 is not None
        assert reported2["retry_count"] == 1
        assert reported2["attempted_models"] == ["gpt-4", "claude-3"]
    finally:
        set_reporter(NoOpReporter())

def test_fallback_api_endpoints():
    client = TestClient(app)
    res_clear = client.post("/v1/fallback/clear")
    assert res_clear.status_code == 200
    assert res_clear.json() == {"success": True}

    trace_id = str(uuid.uuid4())
    res_track1 = client.post("/v1/fallback/track", json={"trace_id": trace_id, "model": "gpt-4"})
    assert res_track1.status_code == 200
    data1 = res_track1.json()
    assert data1["retry_count"] == 0
    assert data1["attempted_models"] == ["gpt-4"]

    res_track2 = client.post("/v1/fallback/track", json={"trace_id": trace_id, "model": "claude-3"})
    assert res_track2.status_code == 200
    data2 = res_track2.json()
    assert data2["retry_count"] == 1
    assert data2["attempted_models"] == ["gpt-4", "claude-3"]

    res_clear2 = client.post("/v1/fallback/clear")
    assert res_clear2.status_code == 200
    assert res_clear2.json() == {"success": True}

    res_track3 = client.post("/v1/fallback/track", json={"trace_id": trace_id, "model": "gpt-4"})
    assert res_track3.status_code == 200
    data3 = res_track3.json()
    assert data3["retry_count"] == 0
    assert data3["attempted_models"] == ["gpt-4"]

