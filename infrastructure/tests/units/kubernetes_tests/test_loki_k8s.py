import pytest
from pathlib import Path
from infrastructure.orchestrator.base.base_kubernetes_activity import YAMLKubernetesManager


LOKI_DEPLOYMENT = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "loki-dynamic-k8s-deployment.yaml"
LOKI_SERVICE = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "loki-dynamic-k8s-service.yaml"


class TestLokiKubernetes:
    
    @pytest.fixture
    def k8s_manager(self):
        return YAMLKubernetesManager(
            yaml_paths=[str(LOKI_DEPLOYMENT), str(LOKI_SERVICE)],
            instance_id=92,
            namespace="default"
        )
    
    def test_manager_initialization(self, k8s_manager):
        assert k8s_manager.instance_id == 92
        assert k8s_manager.namespace == "default"
    
    @pytest.mark.integration
    def test_loki_deployment(self, k8s_manager):
        try:
            k8s_manager.start(restart_if_running=True)
        finally:
            k8s_manager.delete(remove_pvcs=True)
