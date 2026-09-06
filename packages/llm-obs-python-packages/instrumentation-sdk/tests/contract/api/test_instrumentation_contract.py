import pytest
from fastapi.testclient import TestClient

from src.api.rest.v1.app import create_app
from unittest.mock import patch, AsyncMock
import os

# Set env var before importing or using create_app if needed, 
# but here we just call create_app() directly.
os.environ["SKIP_APP_INIT"] = "true"
app = create_app()
client = TestClient(app)


def test_init_endpoint_contract():
    with patch("src.api.rest.v1.handlers.instrumentation.init_auto_instrumentation") as mock_init:
        response = client.post("/v1/instrumentation/init")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert isinstance(data["success"], bool)
        assert isinstance(data["message"], str)
        assert mock_init.called

def test_uninstrument_endpoint_contract():
    with patch("src.api.rest.v1.handlers.instrumentation.uninstrument_all") as mock_uninstrument:
        response = client.post("/v1/instrumentation/uninstrument")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert isinstance(data["success"], bool)
        assert isinstance(data["message"], str)
        assert mock_uninstrument.called

def test_detect_endpoint_contract():
    with patch("src.api.rest.v1.handlers.instrumentation.detect_llm_call") as mock_detect:
        mock_detect.return_value = {"provider": "openai", "model": "gpt-4"}
        payload = {
            "url": "https://api.openai.com/v1/chat/completions",
            "body": '{"model": "gpt-4"}'
        }
        response = client.post("/v1/instrumentation/detect", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "provider" in data
        assert "model" in data
        assert isinstance(data["provider"], str)
        assert isinstance(data["model"], str)

@pytest.mark.asyncio
async def test_test_call_endpoint_contract():
    with patch("src.api.rest.v1.handlers.instrumentation.trigger_test_call", new_callable=AsyncMock) as mock_trigger:
        mock_trigger.return_value = {"success": True, "message": "Triggered"}
        payload = {"method": "httpx", "provider": "openai"}
        response = client.post("/v1/instrumentation/test-call", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert isinstance(data["success"], bool)
        assert isinstance(data["message"], str)

