import pytest
import json
from unittest.mock import patch, MagicMock
from tests.fakes.fake_llm import FakeLLM

def test_chat_completions_success(client):
    fake_llm = FakeLLM(response="OpenAI style response")
    
    with patch("services.api.routes.chat._get_llm_instance", return_value=fake_llm):
        response = client.post("/v1/chat/completions", json={
            "prompt": "Hello",
            "provider": "openai"
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["choices"][0]["message"]["content"] == "OpenAI style response"

def test_chat_simple_success(client):
    fake_llm = FakeLLM(response="Simple response")
    
    with patch("services.api.routes.chat._get_llm_instance", return_value=fake_llm):
        response = client.post("/api/chat", json={
            "prompt": "Hi"
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["response"] == "Simple response"
        assert data["status"] == "success"

def test_chat_no_prompt_error(client):
    response = client.post("/api/chat", json={})
    assert response.status_code == 400
    assert "error" in response.get_json()
