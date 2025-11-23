# infrastructure/observability/activities/log/generate_config_logs.py
import logging
from pathlib import Path
import yaml
import docker
from typing import Dict, Any
from temporalio import activity

logger = logging.getLogger(__name__)

@activity.defn
async def generate_config_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("generate_config_logs started with params: %s", params)

    dynamic_dir = Path(params.get("dynamic_dir"))
    dynamic_dir.mkdir(parents=True, exist_ok=True)
    config_file = dynamic_dir / "otel-collector-generated.yaml"
    loki_push_url = params.get("loki_push_url")

    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)
    except Exception as e:
        logger.error("docker_client_error: %s", str(e))
        return {"success": False, "data": None, "error": "docker_client_error"}

    log_file = dynamic_dir / "container-logs.log"
    log_file.touch(exist_ok=True)
    
    receivers = {
        "filelog": {
            "include": [str(log_file)],
            "start_at": "beginning"
        }
    }

    processors = {
        "batch": {"timeout": "10s"}
    }

    exporters = {
        "loki": {
            "endpoint": loki_push_url
        }
    }

    service_pipelines = {
        "logs": {
            "receivers": ["filelog"],
            "processors": ["batch"],
            "exporters": ["loki"]
        }
    }

    config = {
        "receivers": receivers,
        "processors": processors,
        "exporters": exporters,
        "service": {"pipelines": service_pipelines}
    }

    try:
        with config_file.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(config, fh)
        logger.info("generate_config_logs wrote config: %s", str(config_file))
        return {
            "success": True,
            "data": {"config_path": str(config_file)},
            "error": None
        }
    except Exception as e:
        logger.error("generate_config_logs failed: %s", str(e))
        return {"success": False, "data": None, "error": "generate_failed"}