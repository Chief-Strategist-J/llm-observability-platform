"""End-to-end tests for full workflow."""

import pytest
import httpx
import time
import json
import base64
from typing import Dict, Any


@pytest.mark.e2e
class TestFullWorkflow:
    """End-to-end tests for complete workflows."""
    
    @pytest.fixture
    def api_client(self):
        """HTTP client for API calls."""
        base_url = "http://localhost:8000"
        return httpx.Client(base_url=base_url, timeout=30.0)
    
    @pytest.fixture
    def auth_headers(self):
        """Authentication headers."""
        return {"Authorization": "Bearer test-token"}
    
    def test_complete_event_processing_workflow(self, api_client, auth_headers):
        """Test complete event processing workflow."""
        # 1. Register a schema
        schema_data = {
            "subject": "test-workflow-event",
            "schema": '{"type": "record", "name": "TestEvent", "fields": [{"name": "message", "type": "string"}, {"name": "timestamp", "type": "long"}]}',
            "schema_type": "AVRO"
        }
        
        schema_response = api_client.post(
            "/api/v1/schema-registry/schemas",
            json=schema_data,
            headers=auth_headers
        )
        assert schema_response.status_code == 200
        schema_result = schema_response.json()
        schema_id = schema_result["schema_id"]
        
        # 2. Serialize test data
        serialize_data = {
            "subject": "test-workflow-event",
            "data": {"message": "Hello World", "timestamp": int(time.time() * 1000)}
        }
        
        serialize_response = api_client.post(
            "/api/v1/schema-registry/serialize",
            json=serialize_data,
            headers=auth_headers
        )
        assert serialize_response.status_code == 200
        serialize_result = serialize_response.json()
        serialized_data = serialize_result["data"]
        
        # 3. Store events
        events = [
            {
                "event_id": f"workflow-event-{i}",
                "topic": "test-workflow-topic",
                "partition": 0,
                "offset": i,
                "key": f"key-{i}",
                "value": {"message": f"Test message {i}", "timestamp": int(time.time() * 1000)},
                "timestamp": "2025-01-11T12:00:00Z",
                "headers": {"source": "e2e-test", "version": "1.0"}
            }
            for i in range(3)
        ]
        
        # Store single event
        single_response = api_client.post(
            "/api/v1/database/events",
            json=events[0],
            headers=auth_headers
        )
        assert single_response.status_code == 200
        single_result = single_response.json()
        assert single_result["success"] is True
        
        # Store batch events
        batch_response = api_client.post(
            "/api/v1/database/events/batch",
            json={"records": events[1:]},
            headers=auth_headers
        )
        assert batch_response.status_code == 200
        batch_result = batch_response.json()
        assert batch_result["success"] is True
        assert batch_result["count"] == 2
        
        # 4. Query events
        query_response = api_client.get(
            "/api/v1/database/events?topic=test-workflow-topic&limit=10",
            headers=auth_headers
        )
        assert query_response.status_code == 200
        query_result = query_response.json()
        assert query_result["count"] >= 3
        
        # 5. Get event count
        count_response = api_client.get(
            "/api/v1/database/count?topic=test-workflow-topic",
            headers=auth_headers
        )
        assert count_response.status_code == 200
        count_result = count_response.json()
        assert count_result["count"] >= 3
        
        # 6. Update consumer offset
        offset_data = {
            "consumer_group": "test-workflow-group",
            "topic": "test-workflow-topic",
            "partition": 0,
            "offset": 3
        }
        
        offset_response = api_client.post(
            "/api/v1/database/offsets",
            json=offset_data,
            headers=auth_headers
        )
        assert offset_response.status_code == 200
        offset_result = offset_response.json()
        assert offset_result["consumer_group"] == "test-workflow-group"
        assert offset_result["offset"] == 3
        
        # 7. Get consumer offsets
        get_offsets_response = api_client.get(
            "/api/v1/database/offsets?consumer_group=test-workflow-group&topic=test-workflow-topic",
            headers=auth_headers
        )
        assert get_offsets_response.status_code == 200
        get_offsets_result = get_offsets_response.json()
        assert len(get_offsets_result["offsets"]) >= 1
    
    def test_schema_registry_lifecycle(self, api_client, auth_headers):
        """Test complete schema registry lifecycle."""
        subject = "test-lifecycle-subject"
        
        # 1. Register initial schema
        schema_v1 = {
            "subject": subject,
            "schema": '{"type": "record", "name": "LifecycleEvent", "fields": [{"name": "message", "type": "string"}]}',
            "schema_type": "AVRO"
        }
        
        register_response = api_client.post(
            "/api/v1/schema-registry/schemas",
            json=schema_v1,
            headers=auth_headers
        )
        assert register_response.status_code == 200
        register_result = register_response.json()
        schema_id_v1 = register_result["schema_id"]
        
        # 2. Get schema by subject
        get_response = api_client.get(
            f"/api/v1/schema-registry/schemas/{subject}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        get_result = get_response.json()
        assert get_result["schema_id"] == schema_id_v1
        assert get_result["subject"] == subject
        
        # 3. Check compatibility with compatible schema
        compatible_schema = {
            "subject": subject,
            "schema": '{"type": "record", "name": "LifecycleEvent", "fields": [{"name": "message", "type": "string"}, {"name": "version", "type": "int", "default": 1}]}',
            "schema_type": "AVRO"
        }
        
        compat_response = api_client.post(
            "/api/v1/schema-registry/compatibility",
            json=compatible_schema,
            headers=auth_headers
        )
        assert compat_response.status_code == 200
        compat_result = compat_response.json()
        assert compat_result["is_compatible"] is True
        
        # 4. Update compatibility level
        update_response = api_client.put(
            f"/api/v1/schema-registry/compatibility/{subject}",
            json={"compatibility": "FULL"},
            headers=auth_headers
        )
        assert update_response.status_code == 200
        update_result = update_response.json()
        assert update_result["compatibility"] == "FULL"
        
        # 5. List subjects
        list_response = api_client.get(
            "/api/v1/schema-registry/schemas",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        list_result = list_response.json()
        assert subject in list_result["subjects"]
        
        # 6. Serialize and deserialize data
        test_data = {"message": "Lifecycle test"}
        
        # Serialize
        serialize_request = {
            "subject": subject,
            "data": test_data,
            "schema_id": schema_id_v1
        }
        
        serialize_response = api_client.post(
            "/api/v1/schema-registry/serialize",
            json=serialize_request,
            headers=auth_headers
        )
        assert serialize_response.status_code == 200
        serialize_result = serialize_response.json()
        serialized_data = serialize_result["data"]
        
        # Deserialize
        deserialize_request = {
            "data": serialized_data,
            "schema_id": schema_id_v1
        }
        
        deserialize_response = api_client.post(
            "/api/v1/schema-registry/deserialize",
            json=deserialize_request,
            headers=auth_headers
        )
        assert deserialize_response.status_code == 200
        deserialize_result = deserialize_response.json()
        assert deserialize_result["data"] == test_data
    
    def test_error_handling_workflow(self, api_client, auth_headers):
        """Test error handling throughout workflow."""
        # 1. Invalid event data
        invalid_event = {"topic": ""}  # Missing required fields
        
        invalid_response = api_client.post(
            "/api/v1/database/events",
            json=invalid_event,
            headers=auth_headers
        )
        assert invalid_response.status_code == 400
        invalid_result = invalid_response.json()
        assert "detail" in invalid_result
        assert "error" in invalid_result["detail"]
        
        # 2. Non-existent schema
        schema_response = api_client.get(
            "/api/v1/schema-registry/schemas/non-existent-subject",
            headers=auth_headers
        )
        assert schema_response.status_code == 404
        
        # 3. Invalid schema data
        invalid_schema = {
            "subject": "test-invalid",
            "schema": "invalid json",
            "schema_type": "AVRO"
        }
        
        invalid_schema_response = api_client.post(
            "/api/v1/schema-registry/schemas",
            json=invalid_schema,
            headers=auth_headers
        )
        assert invalid_schema_response.status_code == 400
        
        # 4. Non-existent event
        get_event_response = api_client.get(
            "/api/v1/database/events/non-existent-event-id",
            headers=auth_headers
        )
        # This might return 404 or empty result depending on implementation
        assert get_event_response.status_code in [200, 404]
    
    def test_performance_workflow(self, api_client, auth_headers):
        """Test workflow with performance considerations."""
        # 1. Batch insert performance
        batch_size = 100
        events = [
            {
                "event_id": f"perf-event-{i}",
                "topic": "performance-test-topic",
                "partition": 0,
                "offset": i,
                "key": f"perf-key-{i}",
                "value": {"message": f"Performance test message {i}", "data": "x" * 100},
                "timestamp": "2025-01-11T12:00:00Z"
            }
            for i in range(batch_size)
        ]
        
        start_time = time.time()
        batch_response = api_client.post(
            "/api/v1/database/events/batch",
            json={"records": events},
            headers=auth_headers
        )
        batch_time = time.time() - start_time
        
        assert batch_response.status_code == 200
        batch_result = batch_response.json()
        assert batch_result["success"] is True
        assert batch_result["count"] == batch_size
        
        # Performance assertion (should complete within reasonable time)
        assert batch_time < 5.0, f"Batch insert took too long: {batch_time}s"
        
        # 2. Query performance
        start_time = time.time()
        query_response = api_client.get(
            "/api/v1/database/events?topic=performance-test-topic&limit=50",
            headers=auth_headers
        )
        query_time = time.time() - start_time
        
        assert query_response.status_code == 200
        query_result = query_response.json()
        assert query_result["count"] >= 50
        
        # Performance assertion
        assert query_time < 2.0, f"Query took too long: {query_time}s"
        
        # 3. Count performance
        start_time = time.time()
        count_response = api_client.get(
            "/api/v1/database/count?topic=performance-test-topic",
            headers=auth_headers
        )
        count_time = time.time() - start_time
        
        assert count_response.status_code == 200
        count_result = count_response.json()
        assert count_result["count"] >= batch_size
        
        # Performance assertion
        assert count_time < 1.0, f"Count took too long: {count_time}s"
