import pytest
from pathlib import Path
from infrastructure.orchestrator.base.base_kubernetes_activity import YAMLKubernetesManager, PodState


MONGODB_DEPLOYMENT = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "mongodb-dynamic-k8s-deployment.yaml"
MONGODB_SERVICE = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "mongodb-dynamic-k8s-service.yaml"


class TestMongoDBKubernetes:
    
    @pytest.fixture
    def k8s_manager(self):
        return YAMLKubernetesManager(
            yaml_paths=[str(MONGODB_DEPLOYMENT), str(MONGODB_SERVICE)],
            instance_id=96,
            namespace="default"
        )
    
    def test_manager_initialization(self, k8s_manager):
        assert k8s_manager.instance_id == 96
    
    @pytest.mark.integration
    def test_stateful_service(self, k8s_manager):
        try:
            k8s_manager.start(restart_if_running=True)
            status = k8s_manager.get_status()
            assert status in [PodState.RUNNING, PodState.PENDING, PodState.NOT_FOUND]
        finally:
            k8s_manager.delete(remove_pvcs=True)
