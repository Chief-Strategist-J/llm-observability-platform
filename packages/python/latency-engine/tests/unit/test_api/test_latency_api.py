from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api.rest.v1.app import app
from features.latency_query.types import BaselinePoint, PercentilesResult, SLOResult
from shared.errors.latency_query_errors import (
    BaselineNotFoundError,
    InvalidQuantileError,
    SketchNotFoundError,
    SLODataNotFoundError,
)

# Test JWT secret to use
TEST_SECRET = "my-test-jwt-secret-key-1234"


def generate_test_jwt(sub: str = "test-service", secret: str = TEST_SECRET, expired: bool = False) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    exp = now - 60 if expired else now + 300
    payload = {
        "sub": sub,
        "iat": now,
        "exp": exp,
    }

    def b64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    header_b64 = b64url_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = b64url_encode(json.dumps(payload).encode("utf-8"))

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = b64url_encode(sig)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


@pytest.fixture(autouse=True)
def setup_jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", TEST_SECRET)


@pytest.fixture
def mock_service():
    service = MagicMock()
    app.state.query_service = service
    return service


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# Health Check Endpoint
# ==============================================================================
def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ==============================================================================
# JWT Authentication Tests
# ==============================================================================
def test_auth_missing_header(client):
    resp = client.get("/v1/latency/percentiles?model=gpt-4&hour_of_day=12")
    assert resp.status_code == 401
    assert "detail" in resp.json()


def test_auth_invalid_header_format(client):
    headers = {"Authorization": "invalid-token-format"}
    resp = client.get("/v1/latency/percentiles?model=gpt-4&hour_of_day=12", headers=headers)
    assert resp.status_code == 401


def test_auth_expired_jwt(client):
    token = generate_test_jwt(expired=True)
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/v1/latency/percentiles?model=gpt-4&hour_of_day=12", headers=headers)
    assert resp.status_code == 401
    assert resp.json()["detail"]["error"] == "UNAUTHORIZED"


def test_auth_wrong_secret(client):
    token = generate_test_jwt(secret="wrong-secret-key")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/v1/latency/percentiles?model=gpt-4&hour_of_day=12", headers=headers)
    assert resp.status_code == 401


# ==============================================================================
# Percentiles Endpoint (/v1/latency/percentiles)
# ==============================================================================
def test_get_percentiles_success(client, mock_service):
    mock_service.get_percentiles.return_value = PercentilesResult(
        p50=120.5, p95=450.2, p99=990.0, sample_count=500
    )

    token = generate_test_jwt()
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(
        "/v1/latency/percentiles?model=gpt-4&hour_of_day=12&quantiles=0.50,0.95,0.99",
        headers=headers,
    )

    assert resp.status_code == 200
    assert resp.json() == {"p50": 120.5, "p95": 450.2, "p99": 990.0, "sample_count": 500}
    mock_service.get_percentiles.assert_called_once_with("gpt-4", 12, [0.50, 0.95, 0.99])


def test_get_percentiles_invalid_quantile_param(client, mock_service):
    token = generate_test_jwt()
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(
        "/v1/latency/percentiles?model=gpt-4&hour_of_day=12&quantiles=abc",
        headers=headers,
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"] == "INVALID_PARAM"


def test_get_percentiles_service_invalid_quantile_exception(client, mock_service):
    mock_service.get_percentiles.side_effect = InvalidQuantileError("Quantile out of range")

    token = generate_test_jwt()
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(
        "/v1/latency/percentiles?model=gpt-4&hour_of_day=12&quantiles=0.5,2.0",
        headers=headers,
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"] == "INVALID_PARAM"


def test_get_percentiles_not_found(client, mock_service):
    mock_service.get_percentiles.side_effect = SketchNotFoundError("Sketch not found")

    token = generate_test_jwt()
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(
        "/v1/latency/percentiles?model=gpt-4&hour_of_day=12",
        headers=headers,
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"] == "NOT_FOUND"


# ==============================================================================
# SLO Endpoint (/v1/latency/slo)
# ==============================================================================
def test_get_slo_success(client, mock_service):
    mock_service.get_slo.return_value = SLOResult(
        burn_fast=1.2,
        burn_medium=0.8,
        burn_slow=0.3,
        budget_remaining_pct=95.5,
        slo_threshold_ms=1000.0,
    )

    token = generate_test_jwt()
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(
        "/v1/latency/slo?model=gpt-4&endpoint=/v1/chat/completions",
        headers=headers,
    )

    assert resp.status_code == 200
    assert resp.json() == {
        "burn_fast": 1.2,
        "burn_medium": 0.8,
        "burn_slow": 0.3,
        "budget_remaining_pct": 95.5,
        "slo_threshold_ms": 1000.0,
    }
    mock_service.get_slo.assert_called_once_with("gpt-4", "/v1/chat/completions")


def test_get_slo_not_found(client, mock_service):
    mock_service.get_slo.side_effect = SLODataNotFoundError("SLO data not found")

    token = generate_test_jwt()
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(
        "/v1/latency/slo?model=gpt-4&endpoint=/v1/chat/completions",
        headers=headers,
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"] == "NOT_FOUND"


# ==============================================================================
# Baseline Endpoint (/v1/latency/baseline)
# ==============================================================================
def test_get_baseline_success(client, mock_service):
    from datetime import date

    mock_service.get_baseline.return_value = [
        BaselinePoint(date=date(2026, 6, 24), p99_ttft_ms=110.0, p99_total_ms=900.0),
        BaselinePoint(date=date(2026, 6, 23), p99_ttft_ms=120.0, p99_total_ms=950.0),
    ]

    token = generate_test_jwt()
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(
        "/v1/latency/baseline?model=gpt-4&hour_of_day=12&days=2",
        headers=headers,
    )

    assert resp.status_code == 200
    assert resp.json() == [
        {"date": "2026-06-24", "p99_ttft_ms": 110.0, "p99_total_ms": 900.0},
        {"date": "2026-06-23", "p99_ttft_ms": 120.0, "p99_total_ms": 950.0},
    ]
    mock_service.get_baseline.assert_called_once_with("gpt-4", 12, 2)


def test_get_baseline_not_found(client, mock_service):
    mock_service.get_baseline.side_effect = BaselineNotFoundError("Baseline not found")

    token = generate_test_jwt()
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(
        "/v1/latency/baseline?model=gpt-4&hour_of_day=12",
        headers=headers,
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"] == "NOT_FOUND"


# ==============================================================================
# Attribution Endpoint (/v1/latency/attribution)
# ==============================================================================
def test_get_attribution_success(client, mock_service):
    from features.latency_query.types import AttributionResult

    mock_service.get_attribution.return_value = AttributionResult(
        dns=15.5, tcp=25.0, queue=100.0, inference=800.0
    )

    token = generate_test_jwt()
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(
        "/v1/latency/attribution?model=gpt-4&hour=2026061708",
        headers=headers,
    )

    assert resp.status_code == 200
    assert resp.json() == {
        "dns": 15.5,
        "tcp": 25.0,
        "queue": 100.0,
        "inference": 800.0,
    }
    mock_service.get_attribution.assert_called_once_with("gpt-4", "2026061708")


def test_get_attribution_not_found(client, mock_service):
    from shared.errors.latency_query_errors import AttributionNotFoundError

    mock_service.get_attribution.side_effect = AttributionNotFoundError("Attribution not found")

    token = generate_test_jwt()
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(
        "/v1/latency/attribution?model=gpt-4&hour=2026061708",
        headers=headers,
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"] == "NOT_FOUND"

