import logging
from pathlib import Path
import docker
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig

logger = logging.getLogger(__name__)


class OpenTelemetryCollectorManager(BaseService):
    SERVICE_NAME = "OpenTelemetryCollector"
    SERVICE_DESCRIPTION = "OTel Collector"
    HEALTH_CHECK_TIMEOUT = 30

    def __init__(self):
        dynamic_dir = Path("/home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/dynamicconfig")
        dynamic_dir.mkdir(parents=True, exist_ok=True)

        logs_dir = dynamic_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        for d in (dynamic_dir, logs_dir):
            try:
                d.chmod(0o777)
            except Exception:
                logger.warning("event=otel_dir_permission_failed path=%s", d)

        log_file = logs_dir / "otel-logs.jsonl"
        if log_file.exists():
            try:
                log_file.unlink()
            except Exception:
                logger.warning("event=otel_logfile_remove_failed path=%s", log_file)

        log_file.touch(exist_ok=True)
        try:
            log_file.chmod(0o666)
        except Exception:
            logger.warning("event=otel_logfile_permission_failed path=%s", log_file)

        config = ContainerConfig(
            image="otel/opentelemetry-collector-contrib:0.91.0",
            name="opentelemetry-collector",
            ports={},
            volumes={
                str(dynamic_dir): {"bind": "/etc/otelcol", "mode": "rw"},
                str(logs_dir): {"bind": "/var/log/otelcol", "mode": "rw"},
                "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "ro"}
            },
            network="observability-network",
            restart="unless-stopped",
            extra_hosts={"host.docker.internal": "host-gateway"},
            command=["--config=/etc/otelcol/otel-collector-generated.yaml"],
            labels={
                "traefik.enable": "true",
                "traefik.http.routers.otel.rule": "PathPrefix(`/`)",
                "traefik.http.routers.otel.entrypoints": "otel",
                "traefik.http.routers.otel.service": "otel",
                "traefik.http.services.otel.loadbalancer.server.port": "8888",
                "traefik.docker.network": "observability-network"
            },
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    "wget --no-verbose --tries=1 --spider http://localhost:8888/metrics || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 30000000000
            }
        )

        logger.info(
            "event=otel_manager_init service=otelCollector dynamic_dir=%s logs_dir=%s",
            dynamic_dir, logs_dir
        )

        super().__init__(config)

    def safe_restart(self):
        logger.info("event=otel_safe_restart_begin")
        try:
            self.stop(timeout=10)
        except Exception:
            logger.warning("event=otel_safe_restart_stop_failed")

        try:
            self.run()
            logger.info("event=otel_safe_restart_success")
        except Exception:
            logger.warning("event=otel_container_run_failed_attempting_pull")
            try:
                client = docker.from_env()
                client.images.pull(self.config.image)
                logger.info("event=otel_image_pulled")
            except Exception:
                logger.error("event=otel_image_pull_failed")
            self.run()
            logger.info("event=otel_safe_restart_success_after_pull")


@activity.defn
async def start_opentelemetry_collector(params: dict) -> bool:
    logger.info("event=otel_start params=%s", params)
    mgr = OpenTelemetryCollectorManager()
    mgr.run()
    logger.info("event=otel_started")
    return True


@activity.defn
async def stop_opentelemetry_collector(params: dict) -> bool:
    logger.info("event=otel_stop_begin")
    mgr = OpenTelemetryCollectorManager()
    try:
        mgr.stop(timeout=30)
        logger.info("event=otel_stop_complete")
    except Exception:
        logger.warning("event=otel_stop_failed")
    return True


@activity.defn
async def restart_opentelemetry_collector(params: dict) -> bool:
    logger.info("event=otel_restart_begin")
    mgr = OpenTelemetryCollectorManager()
    mgr.safe_restart()
    logger.info("event=otel_restart_complete")
    return True


@activity.defn
async def delete_opentelemetry_collector(params: dict) -> bool:
    logger.info("event=otel_delete_begin")
    mgr = OpenTelemetryCollectorManager()
    try:
        mgr.delete(force=True)
        logger.info("event=otel_delete_complete")
    except Exception:
        logger.warning("event=otel_delete_failed")
    return True
