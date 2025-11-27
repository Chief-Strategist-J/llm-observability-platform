#!/usr/bin/env python3

from pathlib import Path

ACTIVITY_DIR = Path(__file__).parent.parent / "orchestrator" / "activities" / "configurations_activity"

SERVICES = {
    "grafana": {
        "service_name": "Grafana",
        "yaml_file": "grafana-dynamic-docker.yaml",
        "port_key": "port",
        "port_var": "GRAFANA_PORT",
    },
    "prometheus": {
        "service_name": "Prometheus",
        "yaml_file": "prometheus-dynamic-docker.yaml",
        "port_key": "port",
        "port_var": "PROMETHEUS_PORT",
    },
    "loki": {
        "service_name": "Loki",
        "yaml_file": "loki-dynamic-docker.yaml",
        "port_key": "http_port",
        "port_var": "LOKI_PORT",
    },
    "tempo": {
        "service_name": "Tempo",
        "yaml_file": "tempo-dynamic-docker.yaml",
        "port_key": "http_port",
        "port_var": "TEMPO_PORT",
    },
    "jaeger": {
        "service_name": "Jaeger",
        "yaml_file": "jaeger-dynamic-docker.yaml",
        "port_key": "ui_port",
        "port_var": "JAEGER_UI_PORT",
    },
    "alertmanager": {
        "service_name": "Alertmanager",
        "yaml_file": "alertmanager-docker.yaml",
        "port_key": "port",
        "port_var": "ALERTMANAGER_PORT",
    },
    "kafka": {
        "service_name": "Kafka",
        "yaml_file": "kafka-dynamic-docker.yaml",
        "port_key": "broker_port",
        "port_var": "BROKER_PORT",
        "extra_ports": [("controller_port", "CONTROLLER_PORT")],
    },
    "qdrant": {
        "service_name": "Qdrant",
        "yaml_file": "qdrant-dynamic-docker.yaml",
        "port_key": "http_port",
        "port_var": "QDRANT_HTTP_PORT",
        "extra_ports": [("grpc_port", "QDRANT_GRPC_PORT")],
    },
    "neo4j": {
        "service_name": "Neo4j",
        "yaml_file": "neo4j-dynamic-docker.yaml",
        "port_key": "http_port",
        "port_var": "NEO4J_HTTP_PORT",
        "extra_ports": [("bolt_port", "NEO4J_BOLT_PORT")],
    },
    "mongoexpress": {
        "service_name": "MongoExpress",
        "yaml_file": "mongoexpress-dynamic-docker.yaml",
        "port_key": "port",
        "port_var": "MONGOEXPRESS_PORT",
    },
    "promtail": {
        "service_name": "Promtail",
        "yaml_file": "promtail-dynamic-docker.yaml",
        "port_key": "http_port",
        "port_var": "PROMTAIL_PORT",
    },
    "otel-collector": {
        "service_name": "OtelCollector",
        "yaml_file": "otel-collector-dynamic-docker.yaml",
        "port_key": "http_port",
        "port_var": "OTEL_HTTP_PORT",
        "extra_ports": [("grpc_port", "OTEL_GRPC_PORT")],
    },
    "traefik": {
        "service_name": "Traefik",
        "yaml_file": "traefik-dynamic-docker.yaml",
        "port_key": "http_port",
        "port_var": "HTTP_PORT",
        "extra_ports": [
            ("grafana", "GRAFANA_PORT"),
            ("loki", "LOKI_PORT"),
            ("otel", "OTEL_PORT"),
        ],
    },
}

def generate_activity(service_key, config):
    service_name = config["service_name"]
    class_name = f"{service_name}Manager"
    yaml_file = config["yaml_file"]
    port_key = config["port_key"]
    port_var = config["port_var"]
    extra_ports = config.get("extra_ports", [])
    
    extra_port_lines = ""
    extra_env_vars = ""
    if extra_ports:
        for pk, pv in extra_ports:
            if service_key == "traefik":
                extra_port_lines += f'\n        {pk}_port = pm.get_port("{pk}", instance_id, "port")'
                extra_env_vars += f'\n            "{pv}": str({pk}_port),'
            else:
                extra_port_lines += f'\n        {pk} = pm.get_port("{service_key}", instance_id, "{pk}")'
                extra_env_vars += f'\n            "{pv}": str({pk}),'
    
    return f'''from typing import Dict, Any
from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import YAMLBaseService
from infrastructure.orchestrator.base.port_manager import get_port_manager
from infrastructure.orchestrator.base.logql_logger import LogQLLogger, trace_operation

log = LogQLLogger(__name__)

class {class_name}(YAMLBaseService):
    SERVICE_NAME = "{service_name}"
    SERVICE_DESCRIPTION = "{service_key} service"
    
    _yaml_file_cache = None
    __slots__ = ('_port', '_instance_id')
    
    def __init__(self, instance_id: int = 0) -> None:
        trace_id = log.set_trace_id()
        log.debug("manager_init_start", service="{service_key}", instance=instance_id, trace_id=trace_id)
        
        pm = get_port_manager()
        {service_key}_port = pm.get_port("{service_key}", instance_id, "{port_key}"){extra_port_lines}
        self._port = {service_key}_port
        self._instance_id = instance_id
        
        if not {class_name}._yaml_file_cache:
            {class_name}._yaml_file_cache = Path(__file__).parent.parent.parent / "config" / "docker" / "{yaml_file}"
        
        env_vars = {{
            "{port_var}": str({service_key}_port),{extra_env_vars}
            "INSTANCE_ID": str(instance_id)
        }}
        
        log.debug("yaml_loading", yaml_file=str({class_name}._yaml_file_cache))
        
        super().__init__(
            yaml_file_path={class_name}._yaml_file_cache,
            service_name="{service_key}",
            env_vars=env_vars,
            instance_id=str(instance_id)
        )
        
        log.info("manager_ready", service="{service_key}", instance=instance_id, port={service_key}_port, container=self.config.container_name)

@activity.defn
@trace_operation("start_{service_key}")
async def start_{service_key}_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="start_{service_key}", instance=instance_id)
    {class_name}(instance_id=instance_id).run()
    log.info("activity_complete", activity="start_{service_key}", instance=instance_id)
    return True

@activity.defn
@trace_operation("stop_{service_key}")
async def stop_{service_key}_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="stop_{service_key}", instance=instance_id)
    {class_name}(instance_id=instance_id).stop(timeout=30)
    log.info("activity_complete", activity="stop_{service_key}", instance=instance_id)
    return True

@activity.defn
@trace_operation("restart_{service_key}")
async def restart_{service_key}_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="restart_{service_key}", instance=instance_id)
    {class_name}(instance_id=instance_id).restart()
    log.info("activity_complete", activity="restart_{service_key}", instance=instance_id)
    return True

@activity.defn
@trace_operation("delete_{service_key}")
async def delete_{service_key}_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="delete_{service_key}", instance=instance_id)
    {class_name}(instance_id=instance_id).delete(force=False)
    log.info("activity_complete", activity="delete_{service_key}", instance=instance_id)
    return True
'''

def main():
    print("Generating optimized activity files with LogQL logging...")
    
    for service_key, config in SERVICES.items():
        filename = f"{service_key.replace('-', '_')}_activity.py"
        if service_key == "mongoexpress":
            filename = "mongo_express_activity.py"
        elif service_key == "otel-collector":
            filename = "opentelemetry_collector.py"
        
        filepath = ACTIVITY_DIR / filename
        content = generate_activity(service_key, config)
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"  ✓ Generated {filename}")
    
    print(f"\n✓ Generated {len(SERVICES)} activity files")

if __name__ == "__main__":
    main()
