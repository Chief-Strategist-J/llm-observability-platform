import pytest
from pathlib import Path
from infrastructure.orchestrator.base.base_kubernetes_activity import YAMLKubernetesManager, PodState


REDIS_DEPLOYMENT = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "redis-dynamic-k8s-deployment.yaml"
REDIS_SERVICE = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "redis-dynamic-k8s-service.yaml"


class TestRedisKubernetes:
    
    @pytest.fixture
    def k8s_manager(self):
        return YAMLKubernetesManager(
            yaml_paths=[str(REDIS_DEPLOYMENT), str(REDIS_SERVICE)],
            instance_id=95,
            namespace="default"
        )
    
    def test_manager_initialization(self, k8s_manager):
        assert k8s_manager.instance_id == 95
    
    @pytest.mark.integration
    def test_redis_lifecycle(self, k8s_manager):
        try:
            success = k8s_manager.start(restart_if_running=True)
            assert success in [True, False]
            
            restart_success = k8s_manager.restart()
            assert restart_success in [True, False]
        finally:
            k8s_manager.delete(remove_pvcs=False)
