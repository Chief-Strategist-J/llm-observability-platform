import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

root = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(root))


class TestTracingActivities:
    """Test suite for tracing pipeline activities"""

    @pytest.mark.asyncio
    async def test_configure_source_tracings(self):
        """Test configure_source_tracings activity"""
        from infrastructure.observability.activities.tracing.configure_source_tracings import configure_source_tracings
        
        # Test with valid config path
        params = {
            "config_path": "/tmp/test-config.yaml",
            "dynamic_dir": "/tmp/dynamic",
            "target_name": "test.yaml"
        }
        
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.is_file", return_value=True), \
             patch("shutil.copy2") as mock_copy:
            
            result = await configure_source_tracings(params)
            assert result["success"] == True
            assert "applied_config" in result["data"]

    @pytest.mark.asyncio
    async def test_configure_source_paths_tracings(self):
        """Test configure_source_paths_tracings activity"""
        from infrastructure.observability.activities.tracing.configure_source_paths_tracings import configure_source_paths_tracings
        
        params = {"config_path": "/tmp/test-config.yaml"}
        
        mock_config = """
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
"""
        
        with patch("pathlib.Path.read_text", return_value=mock_config):
            result = await configure_source_paths_tracings(params)
            assert result["success"] == True
            assert "resolved_paths" in result["data"]

    @pytest.mark.asyncio
    async def test_generate_config_tracings(self):
        """Test generate_config_tracings activity"""
        from infrastructure.observability.activities.tracing.generate_config_tracings import generate_config_tracings
        
        params = {
            "dynamic_dir": "/tmp/otelcol",
            "internal_tempo_url": "tempo-dev:4317"
        }
        
        with patch("pathlib.Path.mkdir"), \
             patch("builtins.open", create=True) as mock_open:
            
            result = await generate_config_tracings(params)
            assert result["success"] == True
            assert "config_path" in result["data"]

    @pytest.mark.asyncio
    async def test_deploy_processor_tracings(self):
        """Test deploy_processor_tracings activity"""
        from infrastructure.observability.activities.tracing.deploy_processor_tracings import deploy_processor_tracings
        
        params = {
            "dynamic_dir": "/tmp/otelcol",
            "config_name": "otel-collector-tracings.yaml"
        }
        
        mock_config = """
processors:
  batch:
    timeout: 10s
"""
        
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.read_text", return_value=mock_config):
            
            result = await deploy_processor_tracings(params)
            assert result["success"] == True
            assert result["data"]["processors_present"] == True

    @pytest.mark.asyncio
    async def test_emit_test_event_tracings(self):
        """Test emit_test_event_tracings activity"""
        from infrastructure.observability.activities.tracing.emit_test_event_tracings import emit_test_event_tracings
        
        params = {
            "otlp_endpoint": "http://localhost:4317",
            "service_name": "test-service",
            "span_name": "test-span"
        }
        
        with patch("opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter"), \
             patch("opentelemetry.sdk.trace.TracerProvider"), \
             patch("opentelemetry.sdk.trace.export.BatchSpanProcessor"):
            
            result = await emit_test_event_tracings(params)
            assert result["success"] == True
            assert "token" in result["data"]

    @pytest.mark.asyncio
    async def test_verify_event_ingestion_tracings_success(self):
        """Test verify_event_ingestion_tracings activity - success case"""
        from infrastructure.observability.activities.tracing.verify_event_ingestion_tracings import verify_event_ingestion_tracings
        
        params = {
            "trace_id": "test-trace-123",
            "tempo_query_url": "http://localhost:3200",
            "timeout_seconds": 10,
            "poll_interval": 1.0
        }
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = b'{"batches": [{"spans": [{"traceId": "test-trace-123"}]}]}'
        
        with patch("urllib.request.urlopen", return_value=mock_response):
            result = await verify_event_ingestion_tracings(params)
            assert result["success"] == True
            assert "trace_found" in result["data"]

    @pytest.mark.asyncio
    async def test_verify_event_ingestion_tracings_timeout(self):
        """Test verify_event_ingestion_tracings activity - timeout case"""
        from infrastructure.observability.activities.tracing.verify_event_ingestion_tracings import verify_event_ingestion_tracings
        
        params = {
            "trace_id": "test-trace-123",
            "tempo_query_url": "http://localhost:3200",
            "timeout_seconds": 1,
            "poll_interval": 0.5
        }
        
        # Mock 404 not found
        with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
            result = await verify_event_ingestion_tracings(params)
            assert result["success"] == False
            assert result["error"] in ["tempo_unreachable", "timeout_or_no_match"]

    @pytest.mark.asyncio
    async def test_restart_source_tracings(self):
        """Test restart_source_tracings activity"""
        from infrastructure.observability.activities.tracing.restart_source_tracings import restart_source_tracings
        
        params = {
            "container_name": "otel-collector-test",
            "timeout_seconds": 30
        }
        
        mock_container = MagicMock()
        mock_container.restart = MagicMock()
        mock_container.reload = MagicMock()
        mock_container.status = "running"
        mock_container.attrs = {"State": {"Health": {"Status": "healthy"}}}
        mock_container.logs.return_value = b"Container started successfully"
        
        mock_client = MagicMock()
        mock_client.containers.get.return_value = mock_container
        
        with patch("docker.from_env", return_value=mock_client):
            result = await restart_source_tracings(params)
            assert result["success"] == True
            assert result["data"]["status"] == "running"

    @pytest.mark.asyncio
    async def test_create_grafana_datasource_tracings(self):
        """Test create_grafana_datasource_tracings_activity"""
        from infrastructure.observability.activities.tracing.create_grafana_datasource_tracings_activity import create_grafana_datasource_tracings_activity
        
        params = {
            "grafana_url": "http://localhost:3000",
            "grafana_user": "admin",
            "grafana_password": "admin",
            "datasource_name": "tempo",
            "tempo_url": "http://tempo:3200"
        }
        
        # Mock successful POST response
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.status = 200
        mock_response.read.return_value = b'{"id": 1, "message": "Datasource added"}'
        
        with patch("urllib.request.urlopen", return_value=mock_response):
            result = await create_grafana_datasource_tracings_activity(params)
            assert result["success"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
