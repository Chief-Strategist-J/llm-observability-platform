import pytest
import json
import jwt
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from api.rest.v1.app import (
    app,
    get_redis,
    get_clickhouse,
    get_postgres,
    get_timesfm,
)

def get_auth_headers(secret: str = "super-secret-key") -> dict:
    token = jwt.encode({"sub": "test-service"}, secret, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(autouse=True)
def clean_overrides():
    app.dependency_overrides.clear()
    # Provide default mocks so that actual adapters are never initialized
    app.dependency_overrides[get_redis] = lambda: MagicMock()
    app.dependency_overrides[get_clickhouse] = lambda: MagicMock()
    app.dependency_overrides[get_postgres] = lambda: MagicMock()
    app.dependency_overrides[get_timesfm] = lambda: MagicMock()
    yield
    app.dependency_overrides.clear()

def test_jwt_auth_unauthorized() -> None:
    client = TestClient(app)
    response = client.get("/forecasts/cost/service-a/model-b")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

    response = client.get("/forecasts/cost/service-a/model-b", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401
    assert "Invalid or expired token" in response.json()["detail"]

def test_get_cost_forecast_redis_hit() -> None:
    mock_redis = MagicMock()
    cached_data = {
        "mean": 10000.0,
        "p10": 8000.0,
        "p90": 12000.0,
        "timestamp": "2026-07-07T12:00:00Z"
    }
    mock_redis.client.get.return_value = json.dumps(cached_data).encode("utf-8")
    app.dependency_overrides[get_redis] = lambda: mock_redis

    client = TestClient(app)
    headers = get_auth_headers()
    response = client.get("/forecasts/cost/service-a/model-b", headers=headers)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["service"] == "service-a"
    assert res_data["model"] == "model-b"
    assert res_data["mean"] == 10000.0
    assert res_data["source"] == "redis"

def test_get_cost_forecast_clickhouse_fallback() -> None:
    mock_redis = MagicMock()
    mock_redis.client.get.return_value = None  # Redis miss
    app.dependency_overrides[get_redis] = lambda: mock_redis

    mock_ch = MagicMock()
    now = datetime.utcnow()
    mock_ch.fetch_cost_series_raw.return_value = [
        ("service-a", "model-b", now - timedelta(hours=2), 150.0),
        ("service-a", "model-b", now - timedelta(hours=1), 200.0)
    ]
    app.dependency_overrides[get_clickhouse] = lambda: mock_ch

    mock_timesfm = MagicMock()
    mock_timesfm.forecast.return_value = ([10.0]*24, [8.0]*24, [12.0]*24)
    app.dependency_overrides[get_timesfm] = lambda: mock_timesfm

    client = TestClient(app)
    headers = get_auth_headers()
    response = client.get("/forecasts/cost/service-a/model-b", headers=headers)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["service"] == "service-a"
    assert res_data["model"] == "model-b"
    assert res_data["mean"] == 10.0
    assert res_data["source"] == "clickhouse"
    mock_redis.cache_forecast.assert_called_once()

def test_get_cost_forecast_not_found() -> None:
    mock_redis = MagicMock()
    mock_redis.client.get.return_value = None  # Redis miss
    app.dependency_overrides[get_redis] = lambda: mock_redis

    mock_ch = MagicMock()
    mock_ch.fetch_cost_series_raw.return_value = []  # No data in clickhouse either
    app.dependency_overrides[get_clickhouse] = lambda: mock_ch

    client = TestClient(app)
    headers = get_auth_headers()
    response = client.get("/forecasts/cost/service-a/model-b", headers=headers)

    assert response.status_code == 404
    assert "No historical cost data found" in response.json()["detail"]

def test_get_latency_forecast_redis_hit() -> None:
    mock_redis = MagicMock()
    cached_data = {
        "mean": 45.0,
        "p10": 40.0,
        "p90": 50.0,
        "timestamp": "2026-07-07T12:00:00Z"
    }
    mock_redis.client.get.return_value = json.dumps(cached_data).encode("utf-8")
    app.dependency_overrides[get_redis] = lambda: mock_redis

    client = TestClient(app)
    headers = get_auth_headers()
    response = client.get("/forecasts/latency/service-a/model-b", headers=headers)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["service"] == "service-a"
    assert res_data["model"] == "model-b"
    assert res_data["mean"] == 45.0
    assert res_data["source"] == "redis"

def test_get_cost_breach_risk() -> None:
    mock_redis = MagicMock()
    cached_data = {
        "mean": 12_000_000.0,
        "p10": 9_000_000.0,
        "p90": 15_000_000.0,
        "timestamp": "2026-07-07T12:00:00Z"
    }
    mock_redis.client.get.return_value = json.dumps(cached_data).encode("utf-8")
    app.dependency_overrides[get_redis] = lambda: mock_redis

    mock_pg = MagicMock()
    mock_pg.get_budget_limits.return_value = [("service-a", "model-b", 10.0)] # $10 limit
    app.dependency_overrides[get_postgres] = lambda: mock_pg

    client = TestClient(app)
    headers = get_auth_headers()
    response = client.get("/forecasts/cost/service-a/model-b/breach-risk", headers=headers)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["service"] == "service-a"
    assert res_data["budget_limit"] == 10.0
    assert res_data["predicted_cost_p90_usd"] == 15.0  # 15,000,000 / 1M
    assert res_data["breach_predicted"] is True

    # 2. No breach scenario
    mock_pg.get_budget_limits.return_value = [("service-a", "model-b", 20.0)] # $20 limit
    response = client.get("/forecasts/cost/service-a/model-b/breach-risk", headers=headers)
    assert response.status_code == 200
    assert response.json()["breach_predicted"] is False

    # 3. No budget configured scenario
    mock_pg.get_budget_limits.return_value = []
    response = client.get("/forecasts/cost/service-a/model-b/breach-risk", headers=headers)
    assert response.status_code == 200
    assert response.json()["budget_limit"] is None
    assert response.json()["breach_predicted"] is False

def test_get_forecasts_summary() -> None:
    mock_pg = MagicMock()
    mock_pg.get_all_forecasts.return_value = [
        ("service-a", "model-b", datetime(2026, 7, 7, 12, 0, 0), 12_000_000.0, 9_000_000.0, 15_000_000.0)
    ]
    mock_pg.get_budget_limits.return_value = [("service-a", "model-b", 10.0)]
    app.dependency_overrides[get_postgres] = lambda: mock_pg

    client = TestClient(app)
    headers = get_auth_headers()
    response = client.get("/forecasts/summary", headers=headers)

    assert response.status_code == 200
    res_data = response.json()
    assert len(res_data["forecasts"]) == 1
    item = res_data["forecasts"][0]
    assert item["service"] == "service-a"
    assert item["model"] == "model-b"
    assert item["budget_limit"] == 10.0
    assert item["breach_predicted"] is True
