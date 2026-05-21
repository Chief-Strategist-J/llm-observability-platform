import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os
from src.api.rest.v1.app import create_app

os.environ["SKIP_APP_INIT"] = "true"
app = create_app()
client = TestClient(app)

def test_should_sample_endpoint_contract():
    with patch("src.api.rest.v1.handlers.deterministic_sampling.should_sample") as mock_should_sample:
        mock_should_sample.return_value = True
        payload = {"span_id": "test-span-id"}
        response = client.post("/v1/sampling/should-sample", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "is_sampled" in data
        assert data["is_sampled"] is True
        mock_should_sample.assert_called_once_with("test-span-id")
