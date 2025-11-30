import os
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional
from pathlib import Path


@dataclass
class ServiceEndpoint:
    container_name: str
    internal_host: str
    internal_port: int
    external_port: Optional[int] = None
    traefik_host: Optional[str] = None
    health_path: str = "/health"
    metrics_path: str = "/metrics"
    
    @property
    def internal_url(self) -> str:
        return f"http://{self.internal_host}:{self.internal_port}"
    
    @property
    def external_url(self) -> str:
        if self.external_port:
            return f"http://localhost:{self.external_port}"
        return self.internal_url
    
    @property
    def health_url(self) -> str:
        return f"{self.internal_url}{self.health_path}"
    
    @property
    def metrics_url(self) -> str:
        return f"{self.internal_url}{self.metrics_path}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "container_name": self.container_name,
            "internal_host": self.internal_host,
            "internal_port": self.internal_port,
            "external_port": self.external_port,
            "traefik_host": self.traefik_host,
            "health_path": self.health_path,
            "metrics_path": self.metrics_path,
            "internal_url": self.internal_url,
            "external_url": self.external_url,
            "health_url": self.health_url,
            "metrics_url": self.metrics_url,
        }


@dataclass
class ObservabilityConfig:
    instance_id: str = "0"
    environment: str = "development"
    base_path: str = "/home/j/live/dinesh/llm-chatbot-python"
    
    grafana: ServiceEndpoint = field(default_factory=lambda: ServiceEndpoint(
        container_name="grafana-instance-0",
        internal_host="grafana-instance-0",
        internal_port=3000,
        external_port=31001,
        traefik_host="scaibu.grafana",
        health_path="/api/health",
        metrics_path="/metrics"
    ))
    
    loki: ServiceEndpoint = field(default_factory=lambda: ServiceEndpoint(
        container_name="loki-instance-0",
        internal_host="loki-instance-0",
        internal_port=3100,
        external_port=31002,
        traefik_host="scaibu.loki",
        health_path="/ready",
        metrics_path="/metrics"
    ))
    
    prometheus: ServiceEndpoint = field(default_factory=lambda: ServiceEndpoint(
        container_name="prometheus-instance-0",
        internal_host="prometheus-instance-0",
        internal_port=9090,
        external_port=9090,
        traefik_host="scaibu.prometheus",
        health_path="/-/ready",
        metrics_path="/metrics"
    ))
    
    tempo: ServiceEndpoint = field(default_factory=lambda: ServiceEndpoint(
        container_name="tempo-instance-0",
        internal_host="tempo-instance-0",
        internal_port=3200,
        external_port=31003,
        traefik_host="scaibu.tempo",
        health_path="/ready",
        metrics_path="/metrics"
    ))
    
    otel_collector: ServiceEndpoint = field(default_factory=lambda: ServiceEndpoint(
        container_name="otel-collector-instance-0",
        internal_host="otel-collector-instance-0",
        internal_port=8888,
        external_port=31003,
        traefik_host="scaibu.otel",
        health_path="/metrics",
        metrics_path="/metrics"
    ))
    
    traefik: ServiceEndpoint = field(default_factory=lambda: ServiceEndpoint(
        container_name="traefik-instance-0",
        internal_host="traefik-instance-0",
        internal_port=8080,
        external_port=13101,
        traefik_host=None,
        health_path="/ping",
        metrics_path="/metrics"
    ))
    
    @property
    def otlp_grpc_endpoint(self) -> str:
        return "localhost:4317"
    
    @property
    def otlp_http_endpoint(self) -> str:
        return "localhost:4318"
    
    @property
    def loki_push_url(self) -> str:
        return f"{self.loki.internal_url}/loki/api/v1/push"
    
    @property
    def loki_query_url(self) -> str:
        return f"{self.loki.external_url}/loki/api/v1/query_range"
    
    @property
    def prometheus_query_url(self) -> str:
        return f"{self.prometheus.external_url}/api/v1/query"
    
    @property
    def prometheus_remote_write_url(self) -> str:
        return f"{self.prometheus.internal_url}/api/v1/write"
    
    @property
    def tempo_push_url(self) -> str:
        return f"{self.tempo.internal_host}:4317"
    
    @property
    def tempo_query_url(self) -> str:
        return f"{self.tempo.external_url}/api/traces"
    
    @property
    def grafana_api_url(self) -> str:
        return f"{self.grafana.external_url}/api"
    
    @property
    def dynamic_config_dir(self) -> Path:
        return Path(self.base_path) / "infrastructure" / "orchestrator" / "dynamicconfig"
    
    @property
    def otel_config_dir(self) -> Path:
        return Path(self.base_path) / "infrastructure" / "observability" / "config"
    
    @property
    def otel_logs_dir(self) -> Path:
        return Path(self.base_path) / "infrastructure" / "observability" / "logs"
    
    def get_grafana_datasource_config(self, datasource_type: str) -> Dict[str, Any]:
        configs = {
            "loki": {
                "name": "loki",
                "type": "loki",
                "url": self.loki.internal_url,
                "access": "proxy",
                "isDefault": False,
                "jsonData": {}
            },
            "prometheus": {
                "name": "prometheus",
                "type": "prometheus",
                "url": self.prometheus.internal_url,
                "access": "proxy",
                "isDefault": False,
                "jsonData": {}
            },
            "tempo": {
                "name": "tempo",
                "type": "tempo",
                "url": self.tempo.internal_url,
                "access": "proxy",
                "isDefault": False,
                "jsonData": {}
            }
        }
        return configs.get(datasource_type, {})
    
    def get_otel_config_paths(self) -> Dict[str, str]:
        return {
            "logs": str(self.dynamic_config_dir / "otel-collector-generated.yaml"),
            "metrics": str(self.dynamic_config_dir / "otel-collector-metrics.yaml"),
            "traces": str(self.dynamic_config_dir / "otel-collector-tracings-generated.yaml"),
            "container_logs": "/etc/otelcol/container-logs.log",
        }
    
    def to_workflow_params(self) -> Dict[str, Any]:
        return {
            "dynamic_dir": str(self.dynamic_config_dir),
            "loki_push_url": self.loki_push_url,
            "loki_query_url": self.loki_query_url,
            "prometheus_url": self.prometheus.internal_url,
            "prometheus_query_url": self.prometheus_query_url,
            "tempo_query_url": self.tempo_query_url,
            "tempo_push_url": self.tempo_push_url,
            "grafana_url": self.grafana.external_url,
            "grafana_api_url": self.grafana_api_url,
            "otel_container_name": self.otel_collector.container_name,
            "otlp_grpc_endpoint": self.otlp_grpc_endpoint,
            "otlp_http_endpoint": self.otlp_http_endpoint,
            "grafana_user": os.getenv("GRAFANA_ADMIN_USER", "admin"),
            "grafana_password": os.getenv("GRAFANA_ADMIN_PASSWORD", "SuperSecret123!"),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "environment": self.environment,
            "base_path": self.base_path,
            "grafana": self.grafana.to_dict(),
            "loki": self.loki.to_dict(),
            "prometheus": self.prometheus.to_dict(),
            "tempo": self.tempo.to_dict(),
            "otel_collector": self.otel_collector.to_dict(),
            "traefik": self.traefik.to_dict(),
            "loki_push_url": self.loki_push_url,
            "loki_query_url": self.loki_query_url,
            "prometheus_query_url": self.prometheus_query_url,
            "prometheus_remote_write_url": self.prometheus_remote_write_url,
            "tempo_push_url": self.tempo_push_url,
            "tempo_query_url": self.tempo_query_url,
            "grafana_api_url": self.grafana_api_url,
            "dynamic_config_dir": str(self.dynamic_config_dir),
            "workflow_params": self.to_workflow_params(),
        }


_config_instance: Optional[ObservabilityConfig] = None


def get_observability_config() -> Dict[str, Any]:
    global _config_instance
    if _config_instance is None:
        _config_instance = ObservabilityConfig(
            instance_id=os.getenv("INSTANCE_ID", "0"),
            environment=os.getenv("ENVIRONMENT", "development"),
            base_path=os.getenv("BASE_PATH", "/home/j/live/dinesh/llm-chatbot-python")
        )
    return _config_instance.to_dict()


def reset_observability_config():
    global _config_instance
    _config_instance = None
