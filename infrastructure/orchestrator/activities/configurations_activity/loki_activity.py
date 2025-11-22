import logging
from pathlib import Path
from typing import Optional, Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig

logger = logging.getLogger(__name__)

LOKI_CONFIG_TEXT = """auth_enabled: false

server:
  http_listen_port: 3100
  http_server_read_timeout: 5m
  http_server_write_timeout: 5m

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  wal:
    enabled: true
    dir: /loki/wal

schema_config:
  configs:
    - from: 2020-10-24
      store: tsdb
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  tsdb:
    dir: /loki/tsdb
  boltdb_shipper:
    active_index_directory: /loki/tsdb/index
    cache_location: /loki/boltdb-cache
    shared_store: filesystem
  filesystem:
    directory: /loki/tsdb/chunks

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
"""

class LokiManager(BaseService):
    SERVICE_NAME = "Loki"
    SERVICE_DESCRIPTION = "log aggregation service"
    DEFAULT_PORT = 31002
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self, dynamic_dir: Optional[str] = None, config_override: Optional[str] = None) -> None:
        if dynamic_dir is None:
            dynamic_dir = "/home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/dynamicconfig"
        dynamic_dir_path = Path(dynamic_dir)
        dynamic_dir_path.mkdir(parents=True, exist_ok=True)
        data_dir = dynamic_dir_path / "loki-data"
        data_dir.mkdir(parents=True, exist_ok=True)
        try:
            data_dir.chmod(0o777)
        except Exception:
            pass
        config_file = dynamic_dir_path / "loki-config.yaml"
        if config_override:
            config_text = config_override
        else:
            config_text = LOKI_CONFIG_TEXT
        try:
            config_file.write_text(config_text, encoding="utf-8")
        except Exception:
            pass
        config = ContainerConfig(
            image="grafana/loki:latest",
            name="loki-development",
            ports={3100: 31002},
            volumes={
                str(data_dir): {"bind": "/loki", "mode": "rw"},
                str(config_file): {"bind": "/etc/loki/local-config.yaml", "mode": "ro"},
            },
            network="monitoring-bridge",
            memory="512m",
            memory_reservation="256m",
            cpus=0.5,
            restart="unless-stopped",
            environment={"LOKI_CONFIG_USE_INGRESS": "true"},
            command=["-config.file=/etc/loki/local-config.yaml"],
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    "wget --no-verbose --tries=1 --spider http://localhost:3100/ready || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 40000000000
            }
        )
        extra_data = {"ingress_enabled": "true", "dynamic_dir": str(dynamic_dir_path)}
        super().__init__(config=config, extra=extra_data)
        logger.info("LokiManager initialized (dynamic_dir=%s)", str(dynamic_dir_path))

    def query_logs(self, query: str, limit: int = 100) -> str:
        cmd = f'wget -qO- "http://localhost:3100/loki/api/v1/query?query={query}&limit={limit}"'
        code, out = self.exec(cmd)
        if code != 0:
            logger.error("Failed to query logs: %s", out)
            return ""
        return out

    def get_labels(self) -> str:
        cmd = 'wget -qO- "http://localhost:3100/loki/api/v1/labels"'
        code, out = self.exec(cmd)
        if code != 0:
            logger.error("Failed to get labels: %s", out)
            return ""
        return out

@activity.defn
async def start_loki_activity(params: Dict[str, Any]) -> bool:
    dynamic_dir = params.get("dynamic_dir")
    manager = LokiManager(dynamic_dir=dynamic_dir)
    manager.run()
    return True

@activity.defn
async def stop_loki_activity(params: Dict[str, Any]) -> bool:
    manager = LokiManager(dynamic_dir=params.get("dynamic_dir"))
    manager.stop(timeout=30)
    return True

@activity.defn
async def restart_loki_activity(params: Dict[str, Any]) -> bool:
    manager = LokiManager(dynamic_dir=params.get("dynamic_dir"))
    manager.restart()
    return True

@activity.defn
async def delete_loki_activity(params: Dict[str, Any]) -> bool:
    manager = LokiManager(dynamic_dir=params.get("dynamic_dir"))
    manager.delete(force=False)
    return True
