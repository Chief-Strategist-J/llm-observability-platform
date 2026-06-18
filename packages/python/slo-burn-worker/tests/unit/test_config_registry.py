import pytest
from shared.errors.base import ValidationError
from worker.config import load_config, _int_val, _float_val
from worker.registry import build_registry, WorkflowDefinition, WORKFLOW_REGISTRY

def test_int_val():
    assert _int_val("123", "KEY") == 123
    with pytest.raises(ValidationError):
        _int_val("invalid", "KEY")

def test_float_val():
    assert _float_val("0.95", "KEY") == pytest.approx(0.95)
    with pytest.raises(ValidationError):
        _float_val("invalid", "KEY")

def test_load_config_default():
    cfg = load_config({})
    assert cfg.temporal_host == "localhost:7239"
    assert cfg.clickhouse_port == 8129
    assert cfg.default_slo_compliance == pytest.approx(0.95)

def test_load_config_custom():
    custom_env = {
        "TEMPORAL_HOST": "temporal:7233",
        "TEMPORAL_NAMESPACE": "test-ns",
        "TEMPORAL_TASK_QUEUE": "test-queue",
        "CLICKHOUSE_HOST": "ch-host",
        "CLICKHOUSE_PORT": "9000",
        "CLICKHOUSE_USERNAME": "user",
        "CLICKHOUSE_PASSWORD": "pwd",
        "CLICKHOUSE_DATABASE": "db",
        "REDIS_URL": "redis://redis:6379/1",
        "KAFKA_BOOTSTRAP_SERVERS": "kafka:9092",
        "SLO_COMPLIANCE_CONFIG_PATH": "custom.yaml",
        "DEFAULT_SLO_COMPLIANCE": "0.99"
    }
    cfg = load_config(custom_env)
    assert cfg.temporal_host == "temporal:7233"
    assert cfg.temporal_namespace == "test-ns"
    assert cfg.temporal_task_queue == "test-queue"
    assert cfg.clickhouse_host == "ch-host"
    assert cfg.clickhouse_port == 9000
    assert cfg.clickhouse_username == "user"
    assert cfg.clickhouse_password == "pwd"
    assert cfg.clickhouse_database == "db"
    assert cfg.redis_url == "redis://redis:6379/1"
    assert cfg.kafka_bootstrap_servers == "kafka:9092"
    assert cfg.slo_compliance_config_path == "custom.yaml"
    assert cfg.default_slo_compliance == pytest.approx(0.99)

def test_workflow_registry():
    reg = build_registry()
    assert "slo_burn_computation" in reg
    wf_def = reg["slo_burn_computation"]
    assert isinstance(wf_def, WorkflowDefinition)
    assert wf_def.name == "slo_burn_computation"
    
    assert "slo_burn_computation" in WORKFLOW_REGISTRY
