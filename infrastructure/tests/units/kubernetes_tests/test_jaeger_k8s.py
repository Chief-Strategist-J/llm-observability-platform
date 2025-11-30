import pytest
from pathlib import Path
from infrastructure.orchestrator.base.base_kubernetes_activity import YAMLKubernetesManager, PodState


JAEGER_DEPLOYMENT = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "jaeger-dynamic-k8s-deployment.yaml"
JAEGER_SERVICE = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "jaeger-dynamic-k8s-service.yaml"


class TestJaegerKubernetes:
    
    @pytest.fixture
    def k8s_manager(self):
        return YAMLKubernetesManager(
            yaml_paths=[str(JAEGER_DEPLOYMENT), str(JAEGER_SERVICE)],
            instance_id=97,
            namespace="default"
        )
    
    def test_manager_initialization(self, k8s_manager):
        assert k8s_manager.instance_id == 97
    
    @pytest.mark.integration
    def test_lifecycle(self, k8s_manager):
        try:
            k8s_manager.start(restart_if_running=True)
            assert k8s_manager.get_status() in [PodState.RUNNING, PodState.PENDING, PodState.NOT_FOUND]
        finally:
            k8s_manager.delete(remove_pvcs=True)
