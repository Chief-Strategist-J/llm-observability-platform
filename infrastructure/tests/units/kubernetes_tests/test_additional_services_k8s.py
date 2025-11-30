import pytest
from pathlib import Path
from infrastructure.orchestrator.base.base_kubernetes_activity import YAMLKubernetesManager


ARGOCD_DEPLOYMENT = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "argocd-server-dynamic-k8s-deployment.yaml"
MONGOEXPRESS_DEPLOYMENT = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "mongoexpress-dynamic-k8s-deployment.yaml"
MONGOEXPRESS_SERVICE = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "mongoexpress-dynamic-k8s-service.yaml"
OTEL_DEPLOYMENT = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "otel-collector-dynamic-k8s-deployment.yaml"
OTEL_SERVICE = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "otel-collector-dynamic-k8s-service.yaml"
PROMTAIL_DEPLOYMENT = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "promtail-dynamic-k8s-deployment.yaml"
PROMTAIL_SERVICE = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "promtail-dynamic-k8s-service.yaml"


class TestArgoCDKubernetes:
    
    @pytest.fixture
    def k8s_manager(self):
        return YAMLKubernetesManager(
            yaml_paths=[str(ARGOCD_DEPLOYMENT)],
            instance_id=88,
            namespace="default"
        )
    
    @pytest.mark.integration
    def test_argocd_deployment(self, k8s_manager):
        try:
            k8s_manager.start(restart_if_running=True)
        finally:
            k8s_manager.delete(remove_pvcs=False)


class TestMongoExpressKubernetes:
    
    @pytest.fixture
    def k8s_manager(self):
        return YAMLKubernetesManager(
            yaml_paths=[str(MONGOEXPRESS_DEPLOYMENT), str(MONGOEXPRESS_SERVICE)],
            instance_id=87,
            namespace="default"
        )
    
    @pytest.mark.integration
    def test_mongoexpress_deployment(self, k8s_manager):
        try:
            k8s_manager.start(restart_if_running=True)
        finally:
            k8s_manager.delete(remove_pvcs=False)


class TestOtelCollectorKubernetes:
    
    @pytest.fixture
    def k8s_manager(self):
        return YAMLKubernetesManager(
            yaml_paths=[str(OTEL_DEPLOYMENT), str(OTEL_SERVICE)],
            instance_id=86,
            namespace="default"
        )
    
    @pytest.mark.integration
    def test_otel_collector_deployment(self, k8s_manager):
        try:
            k8s_manager.start(restart_if_running=True)
        finally:
            k8s_manager.delete(remove_pvcs=False)


class TestPromtailKubernetes:
    
    @pytest.fixture
    def k8s_manager(self):
        return YAMLKubernetesManager(
            yaml_paths=[str(PROMTAIL_DEPLOYMENT), str(PROMTAIL_SERVICE)],
            instance_id=85,
            namespace="default"
        )
    
    @pytest.mark.integration
    def test_promtail_deployment(self, k8s_manager):
        try:
            k8s_manager.start(restart_if_running=True)
        finally:
            k8s_manager.delete(remove_pvcs=False)
