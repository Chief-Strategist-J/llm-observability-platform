import logging
from pathlib import Path
from typing import Optional, Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.base.port_manager import get_port_manager

logger = logging.getLogger(__name__)


LOKI_CONFIG_TEMPLATE = """
auth_enabled: false

server:
  http_listen_port: {http_port}
  grpc_listen_port: {grpc_port}

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h

limits_config:
  allow_structured_metadata: true
  volume_enabled: true
  retention_period: 744h
"""


class LokiManager(BaseService):
    SERVICE_NAME = "Loki"
    SERVICE_DESCRIPTION = "log aggregation service"
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self, dynamic_dir: Optional[str] = None, config_override: Optional[str] = None) -> None:
        pm = get_port_manager()

        http_port = pm.get_port("loki", 0, "port")
        grpc_port = pm.get_port("loki", 0, "grpc_port") if "grpc_port" in pm.get_service_info("loki") else http_port + 1

        if dynamic_dir is None:
            dynamic_dir = "/home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/dynamicconfig"

        dynamic_dir_path = Path(dynamic_dir)
        dynamic_dir_path.mkdir(parents=True, exist_ok=True)

        data_dir = dynamic_dir_path / "loki-data"
        data_dir.mkdir(parents=True, exist_ok=True)

        try:
            data_dir.chmod(0o777)
        except Exception as e:
            logger.warning("event=loki_data_chmod_failed error=%s", e)

        config_file = dynamic_dir_path / "loki-config.yaml"

        config_text = config_override if config_override else LOKI_CONFIG_TEMPLATE.format(
            http_port=http_port,
            grpc_port=grpc_port
        )

        try:
            config_file.write_text(config_text, encoding="utf-8")
            config_file.chmod(0o644)

            logger.info(
                "event=loki_config_written file=%s http_port=%s grpc_port=%s",
                str(config_file), http_port, grpc_port
            )

            if not config_file.exists():
                raise RuntimeError(f"Config file missing: {config_file}")

            if not config_file.read_text(encoding="utf-8"):
                raise RuntimeError(f"Config file empty: {config_file}")

        except Exception as e:
            logger.error("event=loki_config_write_failed error=%s", e)
            raise

        config = ContainerConfig(
            image="grafana/loki:latest",
            name="loki-instance-0",
            ports={
                http_port: http_port,
                grpc_port: grpc_port
            },
            volumes={
                str(data_dir.absolute()): {"bind": "/loki", "mode": "rw"},
                str(config_file.absolute()): {"bind": "/etc/loki/local-config.yaml", "mode": "ro"},
            },
            network="observability-network",
            memory="512m",
            memory_reservation="256m",
            cpus=0.5,
            restart="unless-stopped",
            environment={"LOKI_CONFIG_USE_INGRESS": "true"},
            command=["-config.file=/etc/loki/local-config.yaml"],
            labels={
                "traefik.enable": "true",
                "traefik.http.routers.loki.rule": "PathPrefix(`/`)",
                "traefik.http.routers.loki.entrypoints": "loki",
                "traefik.http.routers.loki.service": "loki",
                "traefik.http.services.loki.loadbalancer.server.port": str(http_port),
                "traefik.docker.network": "observability-network",
            },
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    f"wget --no-verbose --tries=1 --spider http://localhost:{http_port}/ready || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 20000000000
            }
        )

        extra_data = {
            "dynamic_dir": str(dynamic_dir_path),
            "http_port": http_port,
            "grpc_port": grpc_port
        }

        super().__init__(config=config, extra=extra_data)

        logger.info(
            "event=loki_manager_initialized http_port=%s grpc_port=%s config_file=%s",
            http_port, grpc_port, str(config_file)
        )

    def query_logs(self, query: str, limit: int = 100) -> str:
        http_port = self.extra.get("http_port")
        cmd = f'wget -qO- "http://localhost:{http_port}/loki/api/v1/query?query={query}&limit={limit}"'
        code, out = self.exec(cmd)

        if code != 0:
            logger.error("event=loki_query_failed error=%s", out)
            return ""

        logger.info("event=loki_query_success limit=%s", limit)
        return out

    def get_labels(self) -> str:
        http_port = self.extra.get("http_port")
        cmd = f'wget -qO- "http://localhost:{http_port}/loki/api/v1/labels"'
        code, out = self.exec(cmd)

        if code != 0:
            logger.error("event=loki_labels_failed error=%s", out)
            return ""

        logger.info("event=loki_labels_success")
        return out


@activity.defn
async def start_loki_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=loki_start params=%s", params)
    manager = LokiManager(dynamic_dir=params.get("dynamic_dir"))
    manager.run()
    logger.info("event=loki_started")
    return True


@activity.defn
async def stop_loki_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=loki_stop params=%s", params)
    manager = LokiManager(dynamic_dir=params.get("dynamic_dir"))
    manager.stop(timeout=30)
    logger.info("event=loki_stopped")
    return True


@activity.defn
async def restart_loki_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=loki_restart params=%s", params)
    manager = LokiManager(dynamic_dir=params.get("dynamic_dir"))
    manager.restart()
    logger.info("event=loki_restarted")
    return True


@activity.defn
async def delete_loki_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=loki_delete params=%s", params)
    manager = LokiManager(dynamic_dir=params.get("dynamic_dir"))
    manager.delete(force=False)
    logger.info("event=loki_deleted")
    return True
