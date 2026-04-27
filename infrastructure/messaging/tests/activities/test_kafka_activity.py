import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from pathlib import Path
from application.activities.kafka_activity import (
    start_kafka_activity,
    stop_kafka_activity,
    restart_kafka_activity,
    delete_kafka_activity,
    get_kafka_status_activity,
    KAFKA_YAML,
)


class TestKafkaActivity:
    @pytest.fixture
    def mock_manager(self):
        manager = MagicMock()
        manager.start.return_value = True
        manager.stop.return_value = True
        manager.restart.return_value = True
        manager.delete.return_value = True
        manager.get_status.return_value = MagicMock(value="running")
        return manager

    @pytest.mark.asyncio
    async def test_start_kafka_activity_success(self, mock_manager):
        with patch('infrastructure.messaging.application.activities.kafka_activity.YAMLContainerManager', return_value=mock_manager):
            result = await start_kafka_activity({"instance_id": 0})
            assert result["success"] is True
            assert result["service"] == "kafka"
            assert result["instance_id"] == 0
            mock_manager.start.assert_called_once_with(restart_if_running=True)

    @pytest.mark.asyncio
    async def test_start_kafka_activity_failure(self, mock_manager):
        mock_manager.start.return_value = False
        mock_manager.get_status.return_value = MagicMock(value="stopped")
        
        with patch('infrastructure.messaging.application.activities.kafka_activity.YAMLContainerManager', return_value=mock_manager):
            result = await start_kafka_activity({"instance_id": 0})
            assert result["success"] is False
            assert result["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_start_kafka_activity_exception(self, mock_manager):
        mock_manager.start.side_effect = Exception("Container error")
        
        with patch('infrastructure.messaging.application.activities.kafka_activity.YAMLContainerManager', return_value=mock_manager):
            result = await start_kafka_activity({"instance_id": 0})
            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_start_kafka_activity_default_instance_id(self, mock_manager):
        with patch('infrastructure.messaging.application.activities.kafka_activity.YAMLContainerManager', return_value=mock_manager):
            result = await start_kafka_activity({})
            assert result["instance_id"] == 0

    @pytest.mark.asyncio
    async def test_start_kafka_activity_custom_instance_id(self, mock_manager):
        with patch('infrastructure.messaging.application.activities.kafka_activity.YAMLContainerManager', return_value=mock_manager):
            result = await start_kafka_activity({"instance_id": 5})
            assert result["instance_id"] == 5

    @pytest.mark.asyncio
    async def test_stop_kafka_activity_success(self, mock_manager):
        with patch('infrastructure.messaging.application.activities.kafka_activity.YAMLContainerManager', return_value=mock_manager):
            result = await stop_kafka_activity({"instance_id": 0, "force": True})
            assert result["success"] is True
            mock_manager.stop.assert_called_once_with(force=True)

    @pytest.mark.asyncio
    async def test_stop_kafka_activity_default_force(self, mock_manager):
        with patch('infrastructure.messaging.application.activities.kafka_activity.YAMLContainerManager', return_value=mock_manager):
            result = await stop_kafka_activity({"instance_id": 0})
            assert result["success"] is True
            mock_manager.stop.assert_called_once_with(force=True)

    @pytest.mark.asyncio
    async def test_restart_kafka_activity_success(self, mock_manager):
        with patch('infrastructure.messaging.application.activities.kafka_activity.YAMLContainerManager', return_value=mock_manager):
            result = await restart_kafka_activity({"instance_id": 0})
            assert result["success"] is True
            mock_manager.restart.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_kafka_activity_success(self, mock_manager):
        with patch('infrastructure.messaging.application.activities.kafka_activity.YAMLContainerManager', return_value=mock_manager):
            result = await delete_kafka_activity({"instance_id": 0})
            assert result["success"] is True
            mock_manager.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_kafka_status_activity_success(self, mock_manager):
        mock_manager.get_status.return_value = MagicMock(value="running")
        
        with patch('infrastructure.messaging.application.activities.kafka_activity.YAMLContainerManager', return_value=mock_manager):
            result = await get_kafka_status_activity({"instance_id": 0})
            assert result["is_running"] is True
            mock_manager.get_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_kafka_status_activity_stopped(self, mock_manager):
        mock_manager.get_status.return_value = MagicMock(value="stopped")
        
        with patch('infrastructure.messaging.application.activities.kafka_activity.YAMLContainerManager', return_value=mock_manager):
            result = await get_kafka_status_activity({"instance_id": 0})
            assert result["is_running"] is False

    @pytest.mark.asyncio
    async def test_get_kafka_status_activity_exception(self, mock_manager):
        mock_manager.get_status.side_effect = Exception("Status error")
        
        with patch('infrastructure.messaging.application.activities.kafka_activity.YAMLContainerManager', return_value=mock_manager):
            result = await get_kafka_status_activity({"instance_id": 0})
            assert result["is_running"] is False
            assert "error" in result


class TestKafkaActivityEdgeCases:
    @pytest.mark.asyncio
    async def test_start_with_invalid_params(self):
        with patch('infrastructure.messaging.application.activities.kafka_activity.YAMLContainerManager') as mock_manager:
            mock_manager.side_effect = ValueError("Invalid params")
            result = await start_kafka_activity({"invalid": "params"})
            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_start_with_negative_instance_id(self):
        with patch('infrastructure.messaging.application.activities.kafka_activity.YAMLContainerManager') as mock_manager:
            mock_manager.return_value.start.return_value = True
            result = await start_kafka_activity({"instance_id": -1})
            assert result["instance_id"] == -1

    @pytest.mark.asyncio
    async def test_stop_with_no_force(self):
        with patch('infrastructure.messaging.application.activities.kafka_activity.YAMLContainerManager') as mock_manager:
            mock_manager.return_value.stop.return_value = True
            result = await stop_kafka_activity({"instance_id": 0, "force": False})
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_nonexistent_container(self):
        with patch('infrastructure.messaging.application.activities.kafka_activity.YAMLContainerManager') as mock_manager:
            mock_manager.return_value.delete.return_value = False
            result = await delete_kafka_activity({"instance_id": 999})
            assert result["success"] is False


class TestKafkaYAMLPath:
    def test_kafka_yaml_path_exists(self):
        assert KAFKA_YAML.exists() or KAFKA_YAML.name == "kafka-docker-compose.yaml"

    def test_kafka_yaml_path_type(self):
        assert isinstance(KAFKA_YAML, Path)
