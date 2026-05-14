"""Unit tests for Database API handlers."""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from kafka_messaging_internal.api.rest.v1.handlers.database import DatabaseAPI, EventRecordRequest, BatchEventRequest, ConsumerOffsetRequest
from kafka_messaging_internal.shared.ports.database_port import DatabasePort


class TestDatabaseAPI:
    """Test cases for Database API handlers"""

    @pytest.fixture
    def mock_database(self):
        """Mock database port"""
        database = Mock(spec=DatabasePort)
        database.save_event = AsyncMock(return_value="test_event_id")
        database.save_events_batch = AsyncMock(return_value=["id1", "id2"])
        database.get_events_by_topic = Mock(return_value=[])
        database.save_consumer_offset = AsyncMock(return_value=True)
        return database

    @pytest.fixture
    def database_api(self, mock_database):
        """Create database API instance"""
        return DatabaseAPI(mock_database)

    @pytest.fixture
    def app(self, database_api):
        """Create FastAPI app for testing"""
        app = FastAPI()
        app.include_router(database_api.get_router(), prefix="/api/v1/database")
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)

    def test_store_event_success(self, client, mock_database):
        """Test successful event storage"""
        request_data = {
            "topic": "test-topic",
            "partition": 0,
            "offset": 123,
            "key": "test-key",
            "value": {"data": "test"}
        }
        
        response = client.post("/api/v1/database/events", json=request_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "event_id" in data
        mock_database.save_event.assert_called_once()

    def test_store_event_validation_error(self, client):
        """Test event storage with invalid data"""
        request_data = {
            "partition": 0,
            "offset": 123,
            "value": {"data": "test"}
            # Missing required 'topic' field
        }
        
        response = client.post("/api/v1/database/events", json=request_data)
        
        assert response.status_code == 422  # Validation error

    def test_query_events_success(self, client, mock_database):
        """Test successful event query"""
        mock_database.get_events_by_topic.return_value = [
            {
                "topic": "test-topic",
                "partition": 0,
                "offset": 123,
                "key": "test-key",
                "value": {"data": "test"}
            }
        ]
        
        response = client.get("/api/v1/database/events", params={"topic": "test-topic", "limit": 10})
        
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "count" in data
        assert "has_more" in data
        mock_database.get_events_by_topic.assert_called_once()

    def test_store_events_batch_success(self, client, mock_database):
        """Test successful batch event storage"""
        request_data = {
            "events": [
                {
                    "topic": "test-topic",
                    "partition": 0,
                    "offset": 123,
                    "key": "test-key",
                    "value": {"data": "test1"}
                },
                {
                    "topic": "test-topic",
                    "partition": 0,
                    "offset": 124,
                    "key": "test-key",
                    "value": {"data": "test2"}
                }
            ]
        }
        
        response = client.post("/api/v1/database/events/batch", json=request_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert "event_ids" in data
        mock_database.save_events_batch.assert_called_once()

    def test_store_events_batch_too_many_events(self, client):
        """Test batch storage with too many events"""
        events = [{"topic": "test", "partition": 0, "offset": i, "value": "test"} 
                  for i in range(1001)]  # Exceeds max limit
        
        request_data = {"events": events}
        
        response = client.post("/api/v1/database/events/batch", json=request_data)
        
        assert response.status_code == 422  # Validation error

    def test_get_consumer_offsets_success(self, client):
        """Test getting consumer offsets"""
        response = client.get("/api/v1/database/offsets?consumer_group=test-group")
        
        assert response.status_code == 200
        data = response.json()
        assert "offsets" in data

    def test_get_consumer_offsets_missing_group(self, client):
        """Test getting offsets without consumer group"""
        response = client.get("/api/v1/database/offsets")
        
        assert response.status_code == 422  # Validation error

    def test_update_consumer_offset_success(self, client, mock_database):
        """Test successful consumer offset update"""
        request_data = {
            "consumer_group": "test-group",
            "topic": "test-topic",
            "partition": 0,
            "offset": 456
        }
        
        response = client.post("/api/v1/database/offsets", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["consumer_group"] == "test-group"
        assert data["topic"] == "test-topic"
        assert data["partition"] == 0
        assert data["offset"] == 456
        mock_database.save_consumer_offset.assert_called_once()

    def test_update_consumer_offset_validation_error(self, client):
        """Test offset update with invalid data"""
        request_data = {
            "consumer_group": "test-group",
            "topic": "test-topic",
            "partition": 0
            # Missing required 'offset' field
        }
        
        response = client.post("/api/v1/database/offsets", json=request_data)
        
        assert response.status_code == 422  # Validation error
