import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
from fastapi.testclient import TestClient

from infra.adapters.clickhouse.clickhouse_adapter import ClickHouseAdapter
from api.rest.v1.app import app


# 1. Tests for ClickHouseAdapter
@patch("clickhouse_connect.get_client")
def test_clickhouse_adapter_fetch_cost(mock_get_client) -> None:
    mock_ch_client = MagicMock()
    mock_get_client.return_value = mock_ch_client
    
    mock_result = MagicMock()
    # Mocking rows returned: service, model, hour_bucket, total_cost
    mock_result.result_rows = [
        ("service-x", "model-y", datetime(2026, 6, 21, 10, 0, 0), 150.0)
    ]
    mock_ch_client.query.return_value = mock_result
    
    adapter = ClickHouseAdapter("host", 8123, "user", "pass", "db")
    rows = adapter.fetch_cost_series_raw(168)
    
    assert len(rows) == 1
    assert rows[0] == ("service-x", "model-y", datetime(2026, 6, 21, 10, 0, 0), 150.0)
    mock_ch_client.query.assert_called_once()


@patch("clickhouse_connect.get_client")
def test_clickhouse_adapter_fetch_latency(mock_get_client) -> None:
    mock_ch_client = MagicMock()
    mock_get_client.return_value = mock_ch_client
    
    mock_result = MagicMock()
    # Mocking rows returned: service, model, hour_bucket, avg_latency
    mock_result.result_rows = [
        ("service-x", "model-y", datetime(2026, 6, 21, 10, 0, 0), 45.5)
    ]
    mock_ch_client.query.return_value = mock_result
    
    adapter = ClickHouseAdapter("host", 8123, "user", "pass", "db")
    rows = adapter.fetch_latency_series_raw(168)
    
    assert len(rows) == 1
    assert rows[0] == ("service-x", "model-y", datetime(2026, 6, 21, 10, 0, 0), 45.5)
    mock_ch_client.query.assert_called_once()


# 2. Tests for FastAPI endpoints in app.py / api.index
@patch("api.rest.v1.app.get_health", new_callable=AsyncMock)
def test_api_health_endpoint(mock_get_health) -> None:
    mock_get_health.return_value = {"status": "ok", "temporal_host": "temporal:7233"}
    
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["temporal_host"] == "temporal:7233"


@patch("api.rest.v1.app.trigger_forecast_workflow", new_callable=AsyncMock)
def test_api_trigger_endpoint_success(mock_trigger) -> None:
    mock_trigger.return_value = {"status": "triggered", "workflow_id": "wf-123"}
    
    client = TestClient(app)
    response = client.post("/trigger", json={"lookback_hours": 72, "min_history_hours": 24})
    
    assert response.status_code == 200
    assert response.json()["status"] == "triggered"
    assert response.json()["workflow_id"] == "wf-123"
    mock_trigger.assert_called_once_with(lookback_hours=72, min_history_hours=24)


@patch("api.rest.v1.app.trigger_forecast_workflow", new_callable=AsyncMock)
def test_api_trigger_endpoint_failure(mock_trigger) -> None:
    mock_trigger.side_effect = Exception("Temporal Connection Error")
    
    client = TestClient(app)
    response = client.post("/trigger", json={"lookback_hours": 72, "min_history_hours": 24})
    
    assert response.status_code == 500
    assert "Temporal Connection Error" in response.json()["detail"]
