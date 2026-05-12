"""Contract tests for API endpoints."""

import pytest
import httpx
import json
import base64
from typing import Dict, Any

from kafka_messaging_internal.api.rest.v1.router import create_app


@pytest.mark.contract
class TestAPIContract:
    """Contract tests for API endpoints."""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        app = create_app()
        return httpx.Client(app=app, base_url="http://test")
    
    def test_health_check_contract(self, client):
        """Test health check endpoint contract."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert data["status"] == "healthy"
        assert data["service"] == "kafka-messaging-internal"
    
    def test_root_endpoint_contract(self, client):
        """Test root endpoint contract."""
        response = client.get("/api/v1/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "redoc" in data
        assert data["message"] == "Kafka Messaging Internal API"
        assert data["version"] == "1.0.0"
    
    def test_store_event_contract(self, client, sample_event_data):
        """Test store event endpoint contract."""
        response = client.post(
            "/api/v1/database/events",
            json=sample_event_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "event_id" in data
        assert "success" in data
        assert "result" in data
        assert "error" in data
        assert data["success"] is True
        assert data["error"] is None
    
    def test_store_event_validation_contract(self, client):
        """Test store event validation contract."""
        invalid_data = {"topic": ""}  # Invalid event
        
        response = client.post(
            "/api/v1/database/events",
            json=invalid_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 400
        data = response.json()
        
        assert "detail" in data
        assert "error" in data["detail"]
        assert "code" in data["detail"]
    
    def test_store_events_batch_contract(self, client, sample_batch_events):
        """Test store events batch endpoint contract."""
        request_data = {"records": sample_batch_events}
        
        response = client.post(
            "/api/v1/database/events/batch",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "event_ids" in data
        assert "count" in data
        assert "success" in data
        assert isinstance(data["event_ids"], list)
        assert data["success"] is True
        assert data["count"] == len(sample_batch_events)
    
    def test_query_events_contract(self, client):
        """Test query events endpoint contract."""
        response = client.get(
            "/api/v1/database/events?topic=test-topic&limit=10&offset=0",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "events" in data
        assert "count" in data
        assert "has_more" in data
        assert isinstance(data["events"], list)
        assert isinstance(data["count"], int)
        assert isinstance(data["has_more"], bool)
    
    def test_register_schema_contract(self, client, sample_schema_data):
        """Test register schema endpoint contract."""
        response = client.post(
            "/api/v1/schema-registry/schemas",
            json=sample_schema_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "schema_id" in data
        assert "subject" in data
        assert "version" in data
        assert "duplicate" in data
        assert isinstance(data["schema_id"], int)
        assert data["subject"] == sample_schema_data["subject"]
    
    def test_list_subjects_contract(self, client):
        """Test list subjects endpoint contract."""
        response = client.get(
            "/api/v1/schema-registry/schemas",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "subjects" in data
        assert isinstance(data["subjects"], list)
    
    def test_get_schema_by_subject_contract(self, client):
        """Test get schema by subject endpoint contract."""
        response = client.get(
            "/api/v1/schema-registry/schemas/test-subject",
            headers={"Authorization": "Bearer test-token"}
        )
        
        # May return 404 if schema doesn't exist, but contract should be consistent
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "subject" in data
            assert "schema_id" in data
            assert "schema_type" in data
            assert "schema" in data
            assert "version" in data
    
    def test_check_compatibility_contract(self, client, sample_schema_data):
        """Test check compatibility endpoint contract."""
        response = client.post(
            "/api/v1/schema-registry/compatibility",
            json=sample_schema_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "is_compatible" in data
        assert "subject" in data
        assert "message" in data
        assert isinstance(data["is_compatible"], bool)
    
    def test_update_compatibility_contract(self, client):
        """Test update compatibility endpoint contract."""
        request_data = {"compatibility": "BACKWARD"}
        
        response = client.put(
            "/api/v1/schema-registry/compatibility/test-subject",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        # May return 404 if subject doesn't exist
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "subject" in data
            assert "compatibility" in data
            assert "message" in data
    
    def test_serialize_data_contract(self, client):
        """Test serialize data endpoint contract."""
        request_data = {
            "subject": "test-subject",
            "data": {"message": "test data"}
        }
        
        response = client.post(
            "/api/v1/schema-registry/serialize",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "schema_id" in data
        assert "subject" in data
        assert isinstance(data["data"], str)  # Base64 encoded
    
    def test_deserialize_data_contract(self, client):
        """Test deserialize data endpoint contract."""
        # Create base64 encoded test data
        test_data = {"message": "test data"}
        encoded_data = base64.b64encode(json.dumps(test_data).encode()).decode()
        
        request_data = {
            "data": encoded_data,
            "schema_id": 1
        }
        
        response = client.post(
            "/api/v1/schema-registry/deserialize",
            json=request_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "schema_id" in data
        assert isinstance(data["schema_id"], int)
    
    def test_get_consumer_offsets_contract(self, client):
        """Test get consumer offsets endpoint contract."""
        response = client.get(
            "/api/v1/database/offsets?consumer_group=test-group",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "offsets" in data
        assert isinstance(data["offsets"], list)
    
    def test_update_consumer_offset_contract(self, client, sample_consumer_offset_data):
        """Test update consumer offset endpoint contract."""
        response = client.post(
            "/api/v1/database/offsets",
            json=sample_consumer_offset_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "consumer_group" in data
        assert "topic" in data
        assert "partition" in data
        assert "offset" in data
        assert "updated_at" in data
        assert data["consumer_group"] == sample_consumer_offset_data["consumer_group"]
    
    def test_get_event_count_contract(self, client):
        """Test get event count endpoint contract."""
        response = client.get(
            "/api/v1/database/count?topic=test-topic",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "count" in data
        assert "topic" in data
        assert isinstance(data["count"], int)
    
    def test_get_unprocessed_events_contract(self, client):
        """Test get unprocessed events endpoint contract."""
        response = client.get(
            "/api/v1/database/unprocessed?limit=10",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "events" in data
        assert "count" in data
        assert "limit" in data
        assert isinstance(data["events"], list)
        assert isinstance(data["count"], int)
        assert isinstance(data["limit"], int)
    
    def test_unauthorized_access_contract(self, client, sample_event_data):
        """Test unauthorized access contract."""
        response = client.post(
            "/api/v1/database/events",
            json=sample_event_data
        )
        
        assert response.status_code == 403
    
    def test_rate_limiting_contract(self, client):
        """Test rate limiting contract (basic check)."""
        # Make multiple requests to test rate limiting
        responses = []
        for _ in range(5):
            response = client.get("/api/v1/health")
            responses.append(response.status_code)
        
        # Most should succeed, rate limiting might kick in after many requests
        assert all(status in [200, 429] for status in responses)
    
    def test_cors_headers_contract(self, client):
        """Test CORS headers contract."""
        response = client.options(
            "/api/v1/database/events",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization"
            }
        )
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
