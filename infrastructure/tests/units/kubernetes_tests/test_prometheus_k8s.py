import pytest
from pathlib import Path
from infrastructure.orchestrator.base.base_kubernetes_activity import YAMLKubernetesManager, PodState


PROMETHEUS_DEPLOYMENT = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "prometheus-dynamic-k8s-deployment.yaml"
PROMETHEUS_SERVICE = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "prometheus-dynamic-k8s-service.yaml"


class TestPrometheusKubernetes:
    
    @pytest.fixture
    def k8s_manager(self):
        return YAMLKubernetesManager(
            yaml_paths=[str(PROMETHEUS_DEPLOYMENT), str(PROMETHEUS_SERVICE)],
            instance_id=98,
            namespace="default"
        )
    
    def test_manager_initialization(self, k8s_manager):
        assert k8s_manager.instance_id == 98
        assert k8s_manager.namespace == "default"
    
    def test_get_status(self, k8s_manager):
        status = k8s_manager.get_status()
        assert isinstance(status, PodState)
    
    @pytest.mark.integration
    def test_start_stop(self, k8s_manager):
        try:
            success = k8s_manager.start(restart_if_running=True)
            assert success in [True, False]
            
            stop_success = k8s_manager.stop(force=True)
            assert stop_success is True
            
        finally:
            k8s_manager.delete(remove_pvcs=True)
