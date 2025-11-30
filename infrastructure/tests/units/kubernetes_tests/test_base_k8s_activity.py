import pytest
from infrastructure.orchestrator.base.base_kubernetes_activity import YAMLKubernetesManager, PodState


class TestBaseKubernetesActivity:
    
    def test_pod_state_enum(self):
        assert PodState.RUNNING.value == "Running"
        assert PodState.PENDING.value == "Pending"
        assert PodState.NOT_FOUND.value == "NotFound"
    
    def test_yaml_config_loader_initialization(self):
        from infrastructure.orchestrator.base.base_kubernetes_activity import YAMLConfigLoader
        from pathlib import Path
        
        yaml_path = Path(__file__).parent.parent.parent.parent / "orchestrator" / "config" / "kubernete" / "grafana-dynamic-k8s-deployment.yaml"
        
        loader = YAMLConfigLoader([str(yaml_path)], instance_id=42, namespace="test-ns")
        assert loader.instance_id == 42
        assert loader.namespace == "test-ns"
        assert len(loader.yaml_paths) == 1
    
    def test_yaml_kubernetes_manager_slots(self):
        manager = YAMLKubernetesManager(
            yaml_paths=["fake.yaml"],
            instance_id=1,
            namespace="default"
        )
        
        assert hasattr(manager, '__slots__')
        
        expected_slots = ['yaml_paths', 'instance_id', 'namespace', 'env_vars', 'log', 'trace_id', 'config', 'port_manager']
        assert all(slot in YAMLKubernetesManager.__slots__ for slot in expected_slots)
