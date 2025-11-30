import os
from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class ObservabilityConstants:
    
    INSTANCE_ID: str = os.getenv("INSTANCE_ID", "0")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    BASE_PATH: str = os.getenv("BASE_PATH", "/home/j/live/dinesh/llm-chatbot-python")
    
    LOKI_CONTAINER: str = f"loki-instance-{os.getenv('INSTANCE_ID', '0')}"
    PROMETHEUS_CONTAINER: str = f"prometheus-instance-{os.getenv('INSTANCE_ID', '0')}"
    TEMPO_CONTAINER: str = f"tempo-instance-{os.getenv('INSTANCE_ID', '0')}"
    GRAFANA_CONTAINER: str = f"grafana-instance-{os.getenv('INSTANCE_ID', '0')}"
    OTEL_COLLECTOR_CONTAINER: str = f"otel-collector-instance-{os.getenv('INSTANCE_ID', '0')}"
    TRAEFIK_CONTAINER: str = f"traefik-instance-{os.getenv('INSTANCE_ID', '0')}"
    
    LOKI_PORT: int = 3100
    PROMETHEUS_PORT: int = 9090
    TEMPO_HTTP_PORT: int = 3200
    TEMPO_GRPC_PORT: int = 4317
    GRAFANA_PORT: int = 3000
    OTEL_METRICS_PORT: int = 8888
    OTEL_GRPC_PORT: int = 4317
    OTEL_HTTP_PORT: int = 4318
    TRAEFIK_DASHBOARD_PORT: int = 8080
    
    LOKI_EXTERNAL_PORT: int = 31002
    PROMETHEUS_EXTERNAL_PORT: int = 9090
    TEMPO_EXTERNAL_PORT: int = 31003
    GRAFANA_EXTERNAL_PORT: int = 31001
    TRAEFIK_HTTP_PORT: int = 13080
    TRAEFIK_HTTPS_PORT: int = 13443
    TRAEFIK_DASHBOARD_EXTERNAL_PORT: int = 13101
    
    @property
    def LOKI_URL(self) -> str:
        return f"http://{self.LOKI_CONTAINER}:{self.LOKI_PORT}"
    
    @property
    def LOKI_PUSH_URL(self) -> str:
        return f"{self.LOKI_URL}/loki/api/v1/push"
    
    @property
    def LOKI_QUERY_URL(self) -> str:
        return f"{self.LOKI_URL}/loki/api/v1/query"
    
    @property
    def LOKI_READY_URL(self) -> str:
        return f"{self.LOKI_URL}/ready"
    
    @property
    def PROMETHEUS_URL(self) -> str:
        return f"http://{self.PROMETHEUS_CONTAINER}:{self.PROMETHEUS_PORT}"
    
    @property
    def PROMETHEUS_WRITE_URL(self) -> str:
        return f"{self.PROMETHEUS_URL}/api/v1/write"
    
    @property
    def PROMETHEUS_QUERY_URL(self) -> str:
        return f"{self.PROMETHEUS_URL}/api/v1/query"
    
    @property
    def PROMETHEUS_READY_URL(self) -> str:
        return f"{self.PROMETHEUS_URL}/-/healthy"
    
    @property
    def TEMPO_URL(self) -> str:
        return f"http://{self.TEMPO_CONTAINER}:{self.TEMPO_HTTP_PORT}"
    
    @property
    def TEMPO_GRPC_URL(self) -> str:
        return f"{self.TEMPO_CONTAINER}:{self.TEMPO_GRPC_PORT}"
    
    @property
    def TEMPO_QUERY_URL(self) -> str:
        return f"{self.TEMPO_URL}/api/traces"
    
    @property
    def TEMPO_READY_URL(self) -> str:
        return f"{self.TEMPO_URL}/ready"
    
    @property
    def GRAFANA_URL(self) -> str:
        return f"http://{self.GRAFANA_CONTAINER}:{self.GRAFANA_PORT}"
    
    @property
    def GRAFANA_API_URL(self) -> str:
        return f"{self.GRAFANA_URL}/api"
    
    @property
    def GRAFANA_HEALTH_URL(self) -> str:
        return f"{self.GRAFANA_URL}/api/health"
    
    @property
    def LOKI_TRAEFIK_URL(self) -> str:
        return "http://scaibu.loki"
    
    @property
    def LOKI_TRAEFIK_ALT_URL(self) -> str:
        return f"http://loki-{self.INSTANCE_ID}.localhost"
    
    @property
    def PROMETHEUS_TRAEFIK_URL(self) -> str:
        return "http://scaibu.prometheus"
    
    @property
    def PROMETHEUS_TRAEFIK_ALT_URL(self) -> str:
        return f"http://prometheus-{self.INSTANCE_ID}.localhost"
    
    @property
    def TEMPO_TRAEFIK_URL(self) -> str:
        return "http://scaibu.tempo"
    
    @property
    def TEMPO_TRAEFIK_ALT_URL(self) -> str:
        return f"http://tempo-{self.INSTANCE_ID}.localhost"
    
    @property
    def GRAFANA_TRAEFIK_URL(self) -> str:
        return "http://scaibu.grafana"
    
    @property
    def GRAFANA_TRAEFIK_ALT_URL(self) -> str:
        return f"http://grafana-{self.INSTANCE_ID}.localhost"
    
    GRAFANA_USER: str = os.getenv("GRAFANA_ADMIN_USER", "admin")
    GRAFANA_PASSWORD: str = os.getenv("GRAFANA_ADMIN_PASSWORD", "SuperSecret123!")
    
    @property
    def DYNAMIC_CONFIG_DIR(self) -> str:
        return f"{self.BASE_PATH}/infrastructure/orchestrator/dynamicconfig"
    
    @property
    def OTEL_CONFIG_FILE_LOGS(self) -> str:
        return f"{self.DYNAMIC_CONFIG_DIR}/otel-collector-generated.yaml"
    
    @property
    def OTEL_CONFIG_FILE_METRICS(self) -> str:
        return f"{self.DYNAMIC_CONFIG_DIR}/otel-collector-metrics.yaml"
    
    @property
    def OTEL_CONFIG_FILE_TRACES(self) -> str:
        return f"{self.DYNAMIC_CONFIG_DIR}/otel-collector-tracings-generated.yaml"
    
    OTLP_GRPC_ENDPOINT: str = "0.0.0.0:4317"
    OTLP_HTTP_ENDPOINT: str = "0.0.0.0:4318"
    
    def get_workflow_params(self) -> Dict[str, Any]:
        return {
            "dynamic_dir": self.DYNAMIC_CONFIG_DIR,
            "loki_push_url": self.LOKI_PUSH_URL,
            "loki_query_url": self.LOKI_QUERY_URL,
            "prometheus_url": self.PROMETHEUS_URL,
            "prometheus_write_url": self.PROMETHEUS_WRITE_URL,
            "prometheus_query_url": self.PROMETHEUS_QUERY_URL,
            "tempo_url": self.TEMPO_URL,
            "tempo_push_url": self.TEMPO_GRPC_URL,
            "tempo_query_url": self.TEMPO_QUERY_URL,
            "internal_tempo_url": self.TEMPO_GRPC_URL,
            "grafana_url": self.GRAFANA_URL,
            "grafana_api_url": self.GRAFANA_API_URL,
            "grafana_user": self.GRAFANA_USER,
            "grafana_password": self.GRAFANA_PASSWORD,
            "otel_container_name": self.OTEL_COLLECTOR_CONTAINER,
            "otlp_grpc_endpoint": self.OTLP_GRPC_ENDPOINT,
            "otlp_http_endpoint": self.OTLP_HTTP_ENDPOINT,
        }
    
    def get_loki_datasource_config(self) -> Dict[str, Any]:
        return {
            "name": "loki",
            "type": "loki",
            "url": self.LOKI_URL,
            "access": "proxy",
            "isDefault": False,
            "jsonData": {}
        }
    
    def get_prometheus_datasource_config(self) -> Dict[str, Any]:
        return {
            "name": "prometheus",
            "type": "prometheus",
            "url": self.PROMETHEUS_URL,
            "access": "proxy",
            "isDefault": False,
            "jsonData": {}
        }
    
    def get_tempo_datasource_config(self) -> Dict[str, Any]:
        return {
            "name": "tempo",
            "type": "tempo",
            "url": self.TEMPO_URL,
            "access": "proxy",
            "isDefault": False,
            "jsonData": {}
        }


OBSERVABILITY_CONFIG = ObservabilityConstants()


def get_config() -> ObservabilityConstants:
    return OBSERVABILITY_CONFIG


def get_loki_url() -> str:
    return OBSERVABILITY_CONFIG.LOKI_URL


def get_prometheus_url() -> str:
    return OBSERVABILITY_CONFIG.PROMETHEUS_URL


def get_tempo_url() -> str:
    return OBSERVABILITY_CONFIG.TEMPO_URL


def get_grafana_url() -> str:
    return OBSERVABILITY_CONFIG.GRAFANA_URL
