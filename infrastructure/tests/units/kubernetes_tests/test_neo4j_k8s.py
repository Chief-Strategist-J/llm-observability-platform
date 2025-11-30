import pytest
from pathlib import Path
from infrastructure.orchestrator.base.base_kubernetes_activity import YAMLKubernetesManager, PodState


NEO4J_DEPLOYMENT = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "neo4j-dynamic-k8s-deployment.yaml"
NEO4J_SERVICE = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "neo4j-dynamic-k8s-service.yaml"


class TestNeo4jKubernetes:
    
    @pytest.fixture
    def k8s_manager(self):
        return YAMLKubernetesManager(
            yaml_paths=[str(NEO4J_DEPLOYMENT), str(NEO4J_SERVICE)],
            instance_id=93,
            namespace="default"
        )
    
    def test_yaml_rendering(self, k8s_manager):
        rendered = k8s_manager._render_yaml_content(NEO4J_DEPLOYMENT)
        assert "neo4j-93" in rendered or "93" in rendered
    
    @pytest.mark.integration
    def test_neo4j_lifecycle(self, k8s_manager):
        try:
            k8s_manager.start(restart_if_running=True)
        finally:
            k8s_manager.delete(remove_pvcs=True)
