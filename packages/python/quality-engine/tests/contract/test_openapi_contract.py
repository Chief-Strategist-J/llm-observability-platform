from __future__ import annotations
import os
import yaml
import pytest
from fastapi.testclient import TestClient
from api.rest.v1.app import app

client = TestClient(app)

@pytest.mark.contract
class TestOpenAPIContract:
    """Contract tests verifying the API matches the contracts/openapi/v1.yaml contract."""

    @pytest.fixture(scope="class")
    def openapi_spec(self) -> dict:
        contract_path = os.path.join(
            os.path.dirname(__file__),
            "../../contracts/openapi/v1.yaml"
        )
        with open(contract_path, "r") as f:
            return yaml.safe_load(f)

    def test_openapi_spec_metadata(self, openapi_spec: dict):
        """Verify contract file metadata exists."""
        assert openapi_spec.get("openapi") is not None
        assert openapi_spec.get("paths") is not None
        assert "HealthResponse" in openapi_spec["components"]["schemas"]
        assert "ScoreRequest" in openapi_spec["components"]["schemas"]
        assert "ScoreResponse" in openapi_spec["components"]["schemas"]

    def test_health_check_contract_parity(self, openapi_spec: dict):
        """Verify the health check endpoint matches the OpenAPI contract."""
        # 1. Check path definition exists in yaml
        assert "/health" in openapi_spec["paths"]

        # 2. Query the actual endpoint
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()

        # 3. Verify response matches HealthResponse schema fields
        health_schema = openapi_spec["components"]["schemas"]["HealthResponse"]
        required_fields = health_schema.get("required", [])
        for field in required_fields:
            assert field in data
        assert isinstance(data["status"], str)

    def test_score_composite_contract_parity(self, openapi_spec: dict):
        """Verify the composite scoring endpoint matches the OpenAPI contract."""
        # 1. Check path definition exists in yaml
        assert "/v1/score/composite" in openapi_spec["paths"]

        # 2. Verify ScoreRequest contract structure
        req_schema = openapi_spec["components"]["schemas"]["ScoreRequest"]
        required_req_fields = req_schema.get("required", [])
        assert "trace_id" in required_req_fields
        assert "span_id" in required_req_fields

        # 3. Post a valid payload matching ScoreRequest contract
        payload = {
            "trace_id": "contract_test_trace",
            "span_id": "contract_test_span",
            "coherence_score": 0.8,
            "faithfulness_score": 0.9,
            "toxicity_score": 0.01,
            "perplexity": 1.8,
            "perplexity_baseline": 2.0,
            "use_literal_formula": False
        }
        resp = client.post("/v1/score/composite", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        # 4. Verify response matches ScoreResponse schema fields
        resp_schema = openapi_spec["components"]["schemas"]["ScoreResponse"]
        required_resp_fields = resp_schema.get("required", [])

        for field in required_resp_fields:
            assert field in data, f"Required response field '{field}' missing from API response"

        # Check types of fields in response
        assert isinstance(data["trace_id"], str)
        assert isinstance(data["span_id"], str)
        assert data["composite_score"] is None or isinstance(data["composite_score"], (int, float))
        assert data["quality_skipped_reason"] is None or isinstance(data["quality_skipped_reason"], str)
        assert isinstance(data["active_weights"], dict)
        assert isinstance(data["raw_contributions"], dict)

    def test_score_composite_validation_error_contract(self):
        """Verify validation errors return 422 as per contract."""
        # Missing required trace_id and span_id
        invalid_payload = {
            "coherence_score": 0.8
        }
        resp = client.post("/v1/score/composite", json=invalid_payload)
        assert resp.status_code == 422
