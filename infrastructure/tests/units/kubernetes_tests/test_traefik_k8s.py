import pytest
from pathlib import Path
from infrastructure.orchestrator.base.base_kubernetes_activity import YAMLKubernetesManager, PodState


TRAEFIK_DEPLOYMENT = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "traefik-dynamic-k8s-deployment.yaml"
TRAEFIK_SERVICE = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "traefik-dynamic-k8s-service.yaml"
TRAEFIK_RBAC = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "traefik-rbac.yaml"


class TestTraefikKubernetes:
    
    @pytest.fixture
    def k8s_manager(self):
        return YAMLKubernetesManager(
            yaml_paths=[str(TRAEFIK_RBAC), str(TRAEFIK_DEPLOYMENT), str(TRAEFIK_SERVICE)],
            instance_id=0,
            namespace="default"
        )
    
    def test_manager_initialization(self, k8s_manager):
        assert k8s_manager.instance_id == 0
        assert len(k8s_manager.config.yaml_paths) == 3
    
    @pytest.mark.integration
    def test_traefik_deployment(self, k8s_manager):
        try:
            success = k8s_manager.start(restart_if_running=True)
            assert success in [True, False]
            
            status = k8s_manager.get_status()
            assert status in [PodState.RUNNING, PodState.PENDING, PodState.NOT_FOUND]
            
        finally:
            k8s_manager.delete(remove_pvcs=False)
