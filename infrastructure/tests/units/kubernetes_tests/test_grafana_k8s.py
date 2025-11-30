import pytest
import asyncio
from pathlib import Path
from infrastructure.orchestrator.base.base_kubernetes_activity import YAMLKubernetesManager, PodState


GRAFANA_DEPLOYMENT = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "grafana-dynamic-k8s-deployment.yaml"
GRAFANA_SERVICE = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "grafana-dynamic-k8s-service.yaml"


class TestGrafanaKubernetes:
    
    @pytest.fixture
    def k8s_manager(self):
        return YAMLKubernetesManager(
            yaml_paths=[str(GRAFANA_DEPLOYMENT), str(GRAFANA_SERVICE)],
            instance_id=99,
            namespace="default",
            env_vars={
                "GRAFANA_ADMIN_USER": "test-admin",
                "GRAFANA_ADMIN_PASSWORD": "test-pass-123",
                "GRAFANA_MEMORY_LIMIT": "512Mi",
                "GRAFANA_CPU_LIMIT": "0.5",
                "GRAFANA_MEMORY_RESERVATION": "256Mi"
            }
        )
    
    def test_manager_initialization(self, k8s_manager):
        assert k8s_manager.instance_id == 99
        assert k8s_manager.namespace == "default"
        assert k8s_manager.config.resource_name == "grafana-99"
    
    def test_env_building(self, k8s_manager):
        env = k8s_manager._build_env()
        assert env["INSTANCE_ID"] == "99"
        assert env["NAMESPACE"] == "default"
        assert env["GRAFANA_ADMIN_USER"] == "test-admin"
    
    def test_yaml_rendering(self, k8s_manager):
        rendered = k8s_manager._render_yaml_content(GRAFANA_DEPLOYMENT)
        assert "grafana-99" in rendered
        assert "test-admin" in rendered
        assert "${INSTANCE_ID}" not in rendered
    
    def test_get_status(self, k8s_manager):
        status = k8s_manager.get_status()
        assert isinstance(status, PodState)
    
    @pytest.mark.integration
    def test_full_lifecycle(self, k8s_manager):
        try:
            success = k8s_manager.start(restart_if_running=True)
            assert success is True or k8s_manager.get_status() == PodState.RUNNING
            
            status = k8s_manager.get_status()
            assert status in [PodState.RUNNING, PodState.PENDING]
            
            scale_success = k8s_manager.scale(replicas=2)
            assert scale_success is True
            
        finally:
            k8s_manager.delete(remove_pvcs=True)
    
    @pytest.mark.integration
    def test_hpa_management(self, k8s_manager):
        try:
            k8s_manager.start(restart_if_running=True)
            
            hpa_created = k8s_manager.create_hpa(min_replicas=1, max_replicas=5, cpu_percent=80)
            assert hpa_created is True
            
            hpa_deleted = k8s_manager.delete_hpa()
            assert hpa_deleted is True
            
        finally:
            k8s_manager.delete(remove_pvcs=True)
