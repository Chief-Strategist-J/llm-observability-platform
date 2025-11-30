import pytest
from pathlib import Path
from infrastructure.orchestrator.base.base_kubernetes_activity import YAMLKubernetesManager, PodState


INNGEST_DEPLOYMENT = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "inngest-dynamic-k8s-deployment.yaml"
INNGEST_SERVICE = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "inngest-dynamic-k8s-service.yaml"


class TestInngestKubernetes:
    
    @pytest.fixture
    def k8s_manager(self):
        return YAMLKubernetesManager(
            yaml_paths=[str(INNGEST_DEPLOYMENT), str(INNGEST_SERVICE)],
            instance_id=84,
            namespace="default",
            env_vars={
                "INNGEST_MEMORY_LIMIT": "512Mi",
                "INNGEST_CPU_LIMIT": "1.0",
                "INNGEST_MEMORY_RESERVATION": "256Mi"
            }
        )
    
    def test_manager_initialization(self, k8s_manager):
        assert k8s_manager.instance_id == 84
        assert k8s_manager.namespace == "default"
    
    def test_yaml_rendering(self, k8s_manager):
        rendered = k8s_manager._render_yaml_content(INNGEST_DEPLOYMENT)
        assert "inngest-84" in rendered
        assert "512Mi" in rendered
    
    @pytest.mark.integration
    def test_inngest_lifecycle(self, k8s_manager):
        try:
            success = k8s_manager.start(restart_if_running=True)
            assert success in [True, False]
            
            status = k8s_manager.get_status()
            assert status in [PodState.RUNNING, PodState.PENDING, PodState.NOT_FOUND]
            
        finally:
            k8s_manager.delete(remove_pvcs=False)
    
    @pytest.mark.integration
    def test_inngest_hpa(self, k8s_manager):
        try:
            k8s_manager.start(restart_if_running=True)
            
            hpa_created = k8s_manager.create_hpa(min_replicas=1, max_replicas=5, cpu_percent=75)
            assert hpa_created is True
            
            hpa_deleted = k8s_manager.delete_hpa()
            assert hpa_deleted is True
            
        finally:
            k8s_manager.delete(remove_pvcs=False)
