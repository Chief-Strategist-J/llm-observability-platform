import logging
from pathlib import Path
import docker
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig

logger = logging.getLogger(__name__)

class OpenTelemetryCollectorManager(BaseService):
    def __init__(self):
        dynamic_dir = Path("/home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/dynamicconfig")
        dynamic_dir.mkdir(parents=True, exist_ok=True)
        logs_dir = dynamic_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        for d in [dynamic_dir, logs_dir]:
            try:
                d.chmod(0o777)
            except Exception:
                pass
        
        log_file = logs_dir / "otel-logs.jsonl"
        if log_file.exists():
            try:
                log_file.unlink()
            except Exception:
                pass
        log_file.touch(exist_ok=True)
        try:
            log_file.chmod(0o666)
        except Exception:
            pass

        config = ContainerConfig(
            image="otel/opentelemetry-collector-contrib:0.91.0",
            name="opentelemetry-collector-development",
            ports={4317: 4317, 4318: 4318, 13133: 13133, 8888: 8888},
            volumes={
                str(dynamic_dir): {"bind": "/etc/otelcol", "mode": "rw"},
                str(logs_dir): {"bind": "/var/log/otelcol", "mode": "rw"},
                "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "ro"}
            },
            network="bridge",
            restart="unless-stopped",
            command=["--config=/etc/otelcol/base.yaml"],
            extra_hosts={"host.docker.internal": "host-gateway"}
        )
        super().__init__(config)

    def safe_restart(self):
        try:
            self.stop(timeout=10)
        except Exception:
            pass
        try:
            self.run()
        except Exception:
            try:
                client = docker.from_env()
                client.images.pull(self.config.image)
            except Exception:
                pass
            self.run()

@activity.defn
async def start_opentelemetry_collector(params: dict) -> bool:
    mgr = OpenTelemetryCollectorManager()
    mgr.run()
    return True

@activity.defn
async def stop_opentelemetry_collector(params: dict) -> bool:
    mgr = OpenTelemetryCollectorManager()
    try:
        mgr.stop(timeout=30)
    except Exception:
        pass
    return True

@activity.defn
async def restart_opentelemetry_collector(params: dict) -> bool:
    mgr = OpenTelemetryCollectorManager()
    mgr.safe_restart()
    return True

@activity.defn
async def delete_opentelemetry_collector(params: dict) -> bool:
    mgr = OpenTelemetryCollectorManager()
    try:
        mgr.delete(force=True)
    except Exception:
        pass
    return True
