import pytest
from fastapi.testclient import TestClient
from src.api.rest.v1.app import app
from unittest.mock import patch, MagicMock, AsyncMock
from src.features.spans.globals import set_reporter, NoOpReporter

client = TestClient(app)

def test_api_reinit_idempotency():
    # Calling /init multiple times should be safe
    response = client.post("/v1/instrumentation/init")
    assert response.status_code == 200
    
    response = client.post("/v1/instrumentation/init")
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_api_detect_malformed_json():
    response = client.post("/v1/instrumentation/detect", content="not-json")
    assert response.status_code == 422

def test_api_detect_missing_fields():
    response = client.post("/v1/instrumentation/detect", json={"url": "only-url"})
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_api_test_call_end_to_end_reporting():
    # Verify that /test-call actually results in a span being reported
    mock_reporter = MagicMock()
    mock_reporter.report_async = AsyncMock()
    set_reporter(mock_reporter)
    
    try:
        # 1. Initialize
        client.post("/v1/instrumentation/init")
        
        # 2. Trigger test call
        payload = {"method": "httpx", "provider": "openai"}
        response = client.post("/v1/instrumentation/test-call", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # 3. Verify span reporting
        # Note: trigger_test_call uses httpx internally, which we've patched.
        # We need to wait a bit or ensure the async call finished.
        # Since TestClient is synchronous but the handler is async, 
        # the response returns AFTER the handler finishes.
        
        assert mock_reporter.report_async.called
        span = mock_reporter.report_async.call_args[0][0]
        assert span["provider"] in ["openai", "http:openai"]
        assert "instrumentation-test-model" in span["model"]
        
    finally:
        client.post("/v1/instrumentation/uninstrument")
        set_reporter(NoOpReporter())

def test_api_uninstrument_when_not_init():
    # Should not crash
    response = client.post("/v1/instrumentation/uninstrument")
    assert response.status_code == 200
    assert response.json()["success"] is True
