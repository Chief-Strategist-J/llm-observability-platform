import pytest
import asyncio
import time
from typing import Optional, Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from src.features.minilm_embedding.ports import EmbeddingClientPort
from src.features.minilm_embedding.infra.adapters.http_embedding_client_adapter import HttpEmbeddingClientAdapter
from src.features.minilm_embedding.service import MiniLMEmbeddingService
from src.features.minilm_embedding.index import get_embedding, enrich_and_report_span
from src.features.spans.globals import set_reporter
from src.api.rest.v1.app import create_app

class MockEmbeddingClient(EmbeddingClientPort):
    def __init__(self, response=None, delay=0.0):
        self.response = response
        self.delay = delay
        self.call_count = 0
        self.last_text = None

    async def embed(self, text: str, timeout_seconds: float) -> Optional[list[float]]:
        self.call_count += 1
        self.last_text = text
        if self.delay > timeout_seconds:
            await asyncio.sleep(timeout_seconds)
            raise asyncio.TimeoutError()
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        return self.response

class MockReporter:
    def __init__(self):
        self.spans = []

    def report(self, span_data):
        self.spans.append(span_data)

    async def report_async(self, span_data):
        self.spans.append(span_data)

@pytest.mark.asyncio
async def test_http_adapter_success():
    adapter = HttpEmbeddingClientAdapter("http://localhost:8000/embed")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        res = await adapter.embed("hello", 0.5)
        assert res == [0.1, 0.2, 0.3]
        mock_post.assert_called_once_with("http://localhost:8000/embed", json={"text": "hello"}, timeout=0.5)

@pytest.mark.asyncio
async def test_http_adapter_error():
    adapter = HttpEmbeddingClientAdapter("http://localhost:8000/embed")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = Exception("Connection error")
        with pytest.raises(Exception):
            await adapter.embed("hello", 0.5)

@pytest.mark.asyncio
async def test_service_success():
    client = MockEmbeddingClient(response=[0.5, 0.6])
    service = MiniLMEmbeddingService(client)
    res = await service.get_embedding("hello")
    assert res == [0.5, 0.6]
    assert client.call_count == 1

@pytest.mark.asyncio
async def test_service_timeout():
    client = MockEmbeddingClient(response=[0.5, 0.6], delay=0.7)
    service = MiniLMEmbeddingService(client)
    res = await service.get_embedding("hello")
    assert res is None

def test_enrich_and_report_span_not_sampled():
    reporter = MockReporter()
    set_reporter(reporter)
    span_data = {
        "span_id": "1",
        "prompt": "hello",
        "is_sampled": False,
        "pii_detected": False
    }
    with patch("src.features.minilm_embedding.index._SERVICE.get_embedding", new_callable=AsyncMock) as mock_get:
        enrich_and_report_span(span_data)
        time.sleep(0.1)
        mock_get.assert_not_called()
        assert len(reporter.spans) == 1
        assert "prompt_embedding" not in reporter.spans[0]

def test_enrich_and_report_span_pii_detected():
    reporter = MockReporter()
    set_reporter(reporter)
    span_data = {
        "span_id": "1",
        "prompt": "hello",
        "is_sampled": True,
        "pii_detected": True
    }
    with patch("src.features.minilm_embedding.index._SERVICE.get_embedding", new_callable=AsyncMock) as mock_get:
        enrich_and_report_span(span_data)
        time.sleep(0.1)
        mock_get.assert_not_called()
        assert len(reporter.spans) == 1
        assert "prompt_embedding" not in reporter.spans[0]

@pytest.mark.asyncio
async def test_enrich_and_report_span_success_async():
    reporter = MockReporter()
    set_reporter(reporter)
    span_data = {
        "span_id": "1",
        "prompt": "hello",
        "is_sampled": True,
        "pii_detected": False
    }
    with patch("src.features.minilm_embedding.index._SERVICE.get_embedding", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [0.1, 0.2]
        enrich_and_report_span(span_data)
        await asyncio.sleep(0.1)
        mock_get.assert_called_once_with("hello")
        assert len(reporter.spans) == 1
        assert reporter.spans[0]["prompt_embedding"] == [0.1, 0.2]

def test_enrich_and_report_span_success_sync():
    reporter = MockReporter()
    set_reporter(reporter)
    span_data = {
        "span_id": "1",
        "prompt": "hello",
        "is_sampled": True,
        "pii_detected": False
    }
    with patch("src.features.minilm_embedding.index._SERVICE.get_embedding", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [0.1, 0.2]
        class SyncThread:
            def __init__(self, target, args=(), kwargs=None):
                self.target = target
                self.args = args
                self.kwargs = kwargs or {}
            def start(self):
                self.target(*self.args, **self.kwargs)
        with patch("threading.Thread", SyncThread):
            enrich_and_report_span(span_data)
        assert len(reporter.spans) == 1
        assert reporter.spans[0]["prompt_embedding"] == [0.1, 0.2]


def test_api_endpoint_success():
    app = create_app()
    client = TestClient(app)
    with patch("src.features.minilm_embedding.index._SERVICE.get_embedding", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = [0.1, 0.2, 0.3]
        response = client.post("/v1/embeddings/embed", json={"text": "hello"})
        assert response.status_code == 200
        assert response.json() == {"embedding": [0.1, 0.2, 0.3]}

def test_api_endpoint_failure():
    app = create_app()
    client = TestClient(app)
    with patch("src.features.minilm_embedding.index._SERVICE.get_embedding", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        response = client.post("/v1/embeddings/embed", json={"text": "hello"})
        assert response.status_code == 500
        assert "Failed to generate embedding" in response.json()["detail"]
