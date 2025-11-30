import pytest
from pathlib import Path
from infrastructure.orchestrator.base.base_kubernetes_activity import YAMLKubernetesManager


TEMPO_DEPLOYMENT = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "tempo-dynamic-k8s-deployment.yaml"
TEMPO_SERVICE = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "tempo-dynamic-k8s-service.yaml"
ALERTMANAGER_DEPLOYMENT = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "alertmanager-dynamic-k8s-deployment.yaml"
ALERTMANAGER_SERVICE = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "alertmanager-dynamic-k8s-service.yaml"
QDRANT_DEPLOYMENT = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "qdrant-dynamic-k8s-deployment.yaml"
QDRANT_SERVICE = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "qdrant-dynamic-k8s-service.yaml"


class TestTempoKubernetes:
    
    @pytest.fixture
    def k8s_manager(self):
        return YAMLKubernetesManager(
            yaml_paths=[str(TEMPO_DEPLOYMENT), str(TEMPO_SERVICE)],
            instance_id=91,
            namespace="default"
        )
    
    @pytest.mark.integration
    def test_tempo_deployment(self, k8s_manager):
        try:
            k8s_manager.start(restart_if_running=True)
        finally:
            k8s_manager.delete(remove_pvcs=True)


class TestAlertmanagerKubernetes:
    
    @pytest.fixture
    def k8s_manager(self):
        return YAMLKubernetesManager(
            yaml_paths=[str(ALERTMANAGER_DEPLOYMENT), str(ALERTMANAGER_SERVICE)],
            instance_id=90,
            namespace="default"
        )
    
    @pytest.mark.integration
    def test_alertmanager_deployment(self, k8s_manager):
        try:
            k8s_manager.start(restart_if_running=True)
        finally:
            k8s_manager.delete(remove_pvcs=True)


class TestQdrantKubernetes:
    
    @pytest.fixture
    def k8s_manager(self):
        return YAMLKubernetesManager(
            yaml_paths=[str(QDRANT_DEPLOYMENT), str(QDRANT_SERVICE)],
            instance_id=89,
            namespace="default"
        )
    
    @pytest.mark.integration
    def test_qdrant_deployment(self, k8s_manager):
        try:
            k8s_manager.start(restart_if_running=True)
        finally:
            k8s_manager.delete(remove_pvcs=True)
