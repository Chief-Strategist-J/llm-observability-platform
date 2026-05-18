import base64
import struct
import pytest
import asyncio
from typing import Any, List
from fastapi.testclient import TestClient
from src import count_tokens, llm_span_with_tokens
from src.features.token_counting.ports import TokenEncoderPort
from src.features.token_counting.service import TokenCountingService
from src.api.rest.v1.app import app

class DummyEncoder(TokenEncoderPort):
    def get_encoding(self, model: str) -> Any:
        if "unknown" in model or "error" in model:
            raise KeyError("Unknown model")
        return "dummy_encoding"

    def encode(self, encoding: Any, text: str) -> List[int]:
        return [1] * len(text.split())

def test_count_tokens_string_tiktoken():
    tokens, method = count_tokens("hello world", "gpt-4")
    assert tokens == 2
    assert method == "tiktoken"

def test_count_tokens_string_estimated():
    tokens, method = count_tokens("hello world", "unknown-model")
    assert tokens == 2
    assert method == "estimated"

def test_heuristic_estimation():
    service = TokenCountingService(DummyEncoder())
    
    tokens_claude, method_claude = service.count_tokens("a" * 35, "claude-unknown")
    assert tokens_claude == 10
    assert method_claude == "estimated"

    tokens_llama, method_llama = service.count_tokens("a" * 33, "meta-llama-unknown")
    assert tokens_llama == 10
    assert method_llama == "estimated"

    tokens_gemini, method_gemini = service.count_tokens("a" * 38, "google-gemini-unknown")
    assert tokens_gemini == 10
    assert method_gemini == "estimated"

    tokens_gpt, method_gpt = service.count_tokens("a" * 40, "unknown-model")
    assert tokens_gpt == 10
    assert method_gpt == "estimated"

def test_image_dimensions_base64():
    service = TokenCountingService(DummyEncoder())

    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(">II", 800, 600) + b"\x08\x06\x00\x00\x00"
    png_url = "data:image/png;base64," + base64.b64encode(png_bytes).decode("utf-8")
    assert service._get_image_dimensions(png_url) == (800, 600)

    gif_bytes = b"GIF89a" + struct.pack("<HH", 300, 400)
    gif_url = "data:image/gif;base64," + base64.b64encode(gif_bytes).decode("utf-8")
    assert service._get_image_dimensions(gif_url) == (300, 400)

    jpeg_bytes = b"\xff\xd8" + b"\xff\xc0" + struct.pack(">H", 8) + b"\x08" + struct.pack(">HH", 500, 700)
    jpeg_url = "data:image/jpeg;base64," + base64.b64encode(jpeg_bytes).decode("utf-8")
    assert service._get_image_dimensions(jpeg_url) == (700, 500)

    assert service._get_image_dimensions("https://example.com/img.png") == (None, None)
    assert service._get_image_dimensions("data:image/png;base64,invalid") == (None, None)

def test_calculate_image_tokens():
    service = TokenCountingService(DummyEncoder())

    assert service._calculate_image_tokens("", "low") == 85

    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(">II", 256, 256) + b"\x08\x06\x00\x00\x00"
    png_url = "data:image/png;base64," + base64.b64encode(png_bytes).decode("utf-8")
    assert service._calculate_image_tokens(png_url, "auto") == 85

    assert service._calculate_image_tokens("https://example.com/img.png", "high") == 765

    png_bytes_high = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(">II", 1024, 1024) + b"\x08\x06\x00\x00\x00"
    png_url_high = "data:image/png;base64," + base64.b64encode(png_bytes_high).decode("utf-8")
    assert service._calculate_image_tokens(png_url_high, "high") == 765

    png_bytes_scale = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(">II", 4096, 2048) + b"\x08\x06\x00\x00\x00"
    png_url_scale = "data:image/png;base64," + base64.b64encode(png_bytes_scale).decode("utf-8")
    assert service._calculate_image_tokens(png_url_scale, "high") == 1105

def test_count_messages_tiktoken():
    service = TokenCountingService(DummyEncoder())

    messages = [
        {"role": "system", "content": "hello assistant"},
        {"role": "user", "content": "how are you"}
    ]
    tokens, method = service.count_tokens(messages, "gpt-4")
    assert tokens == 16
    assert method == "tiktoken"

    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(">II", 1024, 1024) + b"\x08\x06\x00\x00\x00"
    png_url = "data:image/png;base64," + base64.b64encode(png_bytes).decode("utf-8")
    messages_vision = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "describe"},
                {"type": "image_url", "image_url": {"url": png_url, "detail": "high"}}
            ]
        }
    ]
    tokens_v, method_v = service.count_tokens(messages_vision, "gpt-4")
    assert tokens_v == 773
    assert method_v == "tiktoken"

def test_count_messages_estimated():
    service = TokenCountingService(DummyEncoder())

    messages = [
        {"role": "system", "content": "a" * 40},
        {"role": "user", "content": "a" * 20}
    ]
    tokens, method = service.count_tokens(messages, "unknown-model")
    assert tokens == 26
    assert method == "estimated"

def test_span_integration():
    with llm_span_with_tokens(model="gpt-4", provider="openai", prompt="hello world") as span:
        assert span._data["prompt_tokens"] == 2
        assert span._data["token_count_method"] == "tiktoken"

@pytest.mark.asyncio
async def test_span_integration_async():
    async with llm_span_with_tokens(model="gpt-4", provider="openai", prompt="hello world") as span:
        assert span._data["prompt_tokens"] == 2
        assert span._data["token_count_method"] == "tiktoken"

def test_api_endpoint():
    client = TestClient(app)

    response = client.post(
        "/v1/token-counting/count",
        json={"prompt": "hello world", "model": "gpt-4"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tokens"] == 2
    assert data["method"] == "tiktoken"

    response_est = client.post(
        "/v1/token-counting/count",
        json={"prompt": "hello world", "model": "unknown-model"}
    )
    assert response_est.status_code == 200
    data_est = response_est.json()
    assert data_est["tokens"] == 2
    assert data_est["method"] == "estimated"
