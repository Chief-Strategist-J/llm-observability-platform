import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from infrastructure.messaging.application.activities.kafka_ui_activity import (
    start_kafka_ui_activity,
    stop_kafka_ui_activity,
    restart_kafka_ui_activity,
    delete_kafka_ui_activity,
    get_kafka_ui_status_activity,
    KAFKA_UI_YAML,
)


class TestKafkaUIActivity:
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
    async def test_start_kafka_ui_activity_success(self, mock_manager):
        with patch('infrastructure.messaging.application.activities.kafka_ui_activity.YAMLContainerManager', return_value=mock_manager):
            result = await start_kafka_ui_activity({"instance_id": 0})
            assert result["success"] is True
            assert result["service"] == "kafka-ui"
            assert result["instance_id"] == 0
            mock_manager.start.assert_called_once_with(restart_if_running=True)

    @pytest.mark.asyncio
    async def test_start_kafka_ui_activity_failure(self, mock_manager):
        mock_manager.start.return_value = False
        mock_manager.get_status.return_value = MagicMock(value="stopped")
        
        with patch('infrastructure.messaging.application.activities.kafka_ui_activity.YAMLContainerManager', return_value=mock_manager):
            result = await start_kafka_ui_activity({"instance_id": 0})
            assert result["success"] is False
            assert result["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_start_kafka_ui_activity_exception(self, mock_manager):
        mock_manager.start.side_effect = Exception("Container error")
        
        with patch('infrastructure.messaging.application.activities.kafka_ui_activity.YAMLContainerManager', return_value=mock_manager):
            result = await start_kafka_ui_activity({"instance_id": 0})
            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_stop_kafka_ui_activity_success(self, mock_manager):
        with patch('infrastructure.messaging.application.activities.kafka_ui_activity.YAMLContainerManager', return_value=mock_manager):
            result = await stop_kafka_ui_activity({"instance_id": 0, "force": True})
            assert result["success"] is True
            mock_manager.stop.assert_called_once_with(force=True)

    @pytest.mark.asyncio
    async def test_restart_kafka_ui_activity_success(self, mock_manager):
        with patch('infrastructure.messaging.application.activities.kafka_ui_activity.YAMLContainerManager', return_value=mock_manager):
            result = await restart_kafka_ui_activity({"instance_id": 0})
            assert result["success"] is True
            mock_manager.restart.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_kafka_ui_activity_success(self, mock_manager):
        with patch('infrastructure.messaging.application.activities.kafka_ui_activity.YAMLContainerManager', return_value=mock_manager):
            result = await delete_kafka_ui_activity({"instance_id": 0})
            assert result["success"] is True
            mock_manager.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_kafka_ui_status_activity_success(self, mock_manager):
        mock_manager.get_status.return_value = MagicMock(value="running")
        
        with patch('infrastructure.messaging.application.activities.kafka_ui_activity.YAMLContainerManager', return_value=mock_manager):
            result = await get_kafka_ui_status_activity({"instance_id": 0})
            assert result["is_running"] is True
            mock_manager.get_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_kafka_ui_status_activity_stopped(self, mock_manager):
        mock_manager.get_status.return_value = MagicMock(value="stopped")
        
        with patch('infrastructure.messaging.application.activities.kafka_ui_activity.YAMLContainerManager', return_value=mock_manager):
            result = await get_kafka_ui_status_activity({"instance_id": 0})
            assert result["is_running"] is False


class TestKafkaUIActivityEdgeCases:
    @pytest.mark.asyncio
    async def test_start_with_invalid_params(self):
        with patch('infrastructure.messaging.application.activities.kafka_ui_activity.YAMLContainerManager') as mock_manager:
            mock_manager.side_effect = ValueError("Invalid params")
            result = await start_kafka_ui_activity({"invalid": "params"})
            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_delete_nonexistent_container(self):
        with patch('infrastructure.messaging.application.activities.kafka_ui_activity.YAMLContainerManager') as mock_manager:
            mock_manager.return_value.delete.return_value = False
            result = await delete_kafka_ui_activity({"instance_id": 999})
            assert result["success"] is False


class TestKafkaUIYAMLPath:
    def test_kafka_ui_yaml_path_type(self):
        assert isinstance(KAFKA_UI_YAML, Path)
