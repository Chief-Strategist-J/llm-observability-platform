import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from infrastructure.messaging.application.api.inngest_service_api import (
    ServiceRequest,
    BatchServiceRequest,
    ConnectionManager,
    app,
)


class TestServiceRequest:
    def test_service_request_defaults(self):
        request = ServiceRequest()
        assert request.instance_id == 0
        assert request.env_vars is None
        assert request.force is True

    def test_service_request_with_values(self):
        request = ServiceRequest(instance_id=5, env_vars={"KEY": "value"}, force=False)
        assert request.instance_id == 5
        assert request.env_vars == {"KEY": "value"}
        assert request.force is False

    def test_service_request_negative_instance_id(self):
        request = ServiceRequest(instance_id=-1)
        assert request.instance_id == -1

    def test_service_request_large_instance_id(self):
        request = ServiceRequest(instance_id=999999)
        assert request.instance_id == 999999


class TestBatchServiceRequest:
    def test_batch_service_request_defaults(self):
        request = BatchServiceRequest(instance_ids=[0, 1, 2])
        assert request.instance_ids == [0, 1, 2]
        assert request.env_vars is None
        assert request.force is True

    def test_batch_service_request_with_values(self):
        request = BatchServiceRequest(
            instance_ids=[1, 2, 3],
            env_vars={"KEY": "value"},
            force=False
        )
        assert request.instance_ids == [1, 2, 3]
        assert request.env_vars == {"KEY": "value"}
        assert request.force is False

    def test_batch_service_request_empty_list(self):
        request = BatchServiceRequest(instance_ids=[])
        assert request.instance_ids == []

    def test_batch_service_request_single_instance(self):
        request = BatchServiceRequest(instance_ids=[5])
        assert request.instance_ids == [5]


class TestConnectionManager:
    @pytest.fixture
    def manager(self):
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        websocket = MagicMock()
        websocket.accept = AsyncMock()
        return websocket

    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_websocket):
        await manager.connect(mock_websocket)
        assert mock_websocket in manager.active_connections
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        manager.active_connections.append(mock_websocket)
        manager.disconnect(mock_websocket)
        assert mock_websocket not in manager.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent(self, manager, mock_websocket):
        manager.disconnect(mock_websocket)
        assert mock_websocket not in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast(self, manager, mock_websocket):
        mock_websocket.send_json = AsyncMock()
        manager.active_connections.append(mock_websocket)
        
        message = {"test": "data"}
        await manager.broadcast(message)
        
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert "timestamp" in call_args
        assert call_args["test"] == "data"

    @pytest.mark.asyncio
    async def test_broadcast_multiple_connections(self, manager):
        ws1 = MagicMock()
        ws2 = MagicMock()
        ws1.send_json = AsyncMock()
        ws2.send_json = AsyncMock()
        
        manager.active_connections.extend([ws1, ws2])
        
        message = {"test": "data"}
        await manager.broadcast(message)
        
        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_dead_connection(self, manager, mock_websocket):
        mock_websocket.send_json = AsyncMock(side_effect=Exception("Connection dead"))
        manager.active_connections.append(mock_websocket)
        
        message = {"test": "data"}
        await manager.broadcast(message)
        
        assert mock_websocket not in manager.active_connections


class TestInngestServiceAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_observability_client(self):
        with patch('infrastructure.messaging.application.api.inngest_service_api.ObservabilityClient') as mock:
            yield mock.return_value

    def test_start_service_endpoint(self, client, mock_observability_client):
        with patch('infrastructure.messaging.application.api.inngest_service_api.start_inngest_activity', new_callable=AsyncMock) as mock_activity:
            mock_activity.return_value = {"success": True, "service": "inngest", "instance_id": 0}
            
            response = client.post("/start", json={"instance_id": 0})
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_start_service_endpoint_failure(self, client, mock_observability_client):
        with patch('infrastructure.messaging.application.api.inngest_service_api.start_inngest_activity', new_callable=AsyncMock) as mock_activity:
            mock_activity.return_value = {"success": False, "error": "Failed to start"}
            
            response = client.post("/start", json={"instance_id": 0})
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False

    def test_stop_service_endpoint(self, client, mock_observability_client):
        with patch('infrastructure.messaging.application.api.inngest_service_api.stop_inngest_activity', new_callable=AsyncMock) as mock_activity:
            mock_activity.return_value = {"success": True, "service": "inngest", "instance_id": 0}
            
            response = client.post("/stop", json={"instance_id": 0, "force": True})
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_restart_service_endpoint(self, client, mock_observability_client):
        with patch('infrastructure.messaging.application.api.inngest_service_api.restart_inngest_activity', new_callable=AsyncMock) as mock_activity:
            mock_activity.return_value = {"success": True, "service": "inngest", "instance_id": 0}
            
            response = client.post("/restart", json={"instance_id": 0})
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_delete_service_endpoint(self, client, mock_observability_client):
        with patch('infrastructure.messaging.application.api.inngest_service_api.delete_inngest_activity', new_callable=AsyncMock) as mock_activity:
            mock_activity.return_value = {"success": True, "service": "inngest", "instance_id": 0}
            
            response = client.post("/delete", json={"instance_id": 0})
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_status_service_endpoint(self, client, mock_observability_client):
        with patch('infrastructure.messaging.application.api.inngest_service_api.get_inngest_status_activity', new_callable=AsyncMock) as mock_activity:
            mock_activity.return_value = {"is_running": True, "service": "inngest", "instance_id": 0}
            
            response = client.get("/status/0")
            assert response.status_code == 200
            data = response.json()
            assert data["is_running"] is True

    def test_batch_start_endpoint(self, client, mock_observability_client):
        with patch('infrastructure.messaging.application.api.inngest_service_api.start_inngest_activity', new_callable=AsyncMock) as mock_activity:
            mock_activity.return_value = {"success": True, "service": "inngest", "instance_id": 0}
            
            response = client.post("/batch/start", json={"instance_ids": [0, 1, 2]})
            assert response.status_code == 200
            data = response.json()
            assert "results" in data

    def test_invalid_json_request(self, client):
        response = client.post("/start", json={"invalid": "data"})
        assert response.status_code in [200, 422]

    def test_missing_instance_id(self, client):
        response = client.post("/start", json={})
        assert response.status_code in [200, 422]

    def test_negative_instance_id(self, client, mock_observability_client):
        with patch('infrastructure.messaging.application.api.inngest_service_api.start_inngest_activity', new_callable=AsyncMock) as mock_activity:
            mock_activity.return_value = {"success": True, "service": "inngest", "instance_id": -1}
            
            response = client.post("/start", json={"instance_id": -1})
            assert response.status_code == 200

    def test_large_instance_id(self, client, mock_observability_client):
        with patch('infrastructure.messaging.application.api.inngest_service_api.start_inngest_activity', new_callable=AsyncMock) as mock_activity:
            mock_activity.return_value = {"success": True, "service": "inngest", "instance_id": 999999}
            
            response = client.post("/start", json={"instance_id": 999999})
            assert response.status_code == 200


class TestAPIEdgeCases:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_activity_exception_handling(self, client):
        with patch('infrastructure.messaging.application.api.inngest_service_api.start_inngest_activity', new_callable=AsyncMock) as mock_activity:
            mock_activity.side_effect = Exception("Activity error")
            
            response = client.post("/start", json={"instance_id": 0})
            assert response.status_code == 200
            data = response.json()
            assert "error" in data or "success" in data

    def test_concurrent_requests(self, client):
        with patch('infrastructure.messaging.application.api.inngest_service_api.start_inngest_activity', new_callable=AsyncMock) as mock_activity:
            mock_activity.return_value = {"success": True, "service": "inngest", "instance_id": 0}
            
            import asyncio
            async def make_request():
                return client.post("/start", json={"instance_id": 0})
            
            results = asyncio.run(asyncio.gather(make_request(), make_request(), make_request()))
            assert all(r.status_code == 200 for r in results)

    def test_env_vars_injection(self, client):
        with patch('infrastructure.messaging.application.api.inngest_service_api.start_inngest_activity', new_callable=AsyncMock) as mock_activity:
            mock_activity.return_value = {"success": True, "service": "inngest", "instance_id": 0}
            
            response = client.post("/start", json={"instance_id": 0, "env_vars": {"KEY": "value"}})
            assert response.status_code == 200

    def test_force_flag_true(self, client):
        with patch('infrastructure.messaging.application.api.inngest_service_api.stop_inngest_activity', new_callable=AsyncMock) as mock_activity:
            mock_activity.return_value = {"success": True, "service": "inngest", "instance_id": 0}
            
            response = client.post("/stop", json={"instance_id": 0, "force": True})
            assert response.status_code == 200

    def test_force_flag_false(self, client):
        with patch('infrastructure.messaging.application.api.inngest_service_api.stop_inngest_activity', new_callable=AsyncMock) as mock_activity:
            mock_activity.return_value = {"success": True, "service": "inngest", "instance_id": 0}
            
            response = client.post("/stop", json={"instance_id": 0, "force": False})
            assert response.status_code == 200
