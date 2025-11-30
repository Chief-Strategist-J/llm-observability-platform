import logging
from pathlib import Path
from typing import Dict, Any
from temporalio import activity
import yaml
from infrastructure.observability.config.constants import OBSERVABILITY_CONFIG

logger = logging.getLogger(__name__)

@activity.defn
async def generate_config_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("generate_config_logs_start params_keys=%s", list(params.keys()))

    dynamic_dir = Path(params.get("dynamic_dir", "/etc/otelcol/generated"))
    dynamic_dir.mkdir(parents=True, exist_ok=True)
    logger.debug("generate_config_logs_dir dir=%s", dynamic_dir)

    config_file = dynamic_dir / "otel-collector-generated.yaml"
    
    loki_push_url = params.get("loki_push_url", OBSERVABILITY_CONFIG.LOKI_PUSH_URL)
    
    internal_loki_url = OBSERVABILITY_CONFIG.LOKI_PUSH_URL
    
    logger.info("generate_config_logs_loki_url url=%s", loki_push_url)
    
    container_log_path = params.get("container_log_path", "/etc/otelcol/container-logs.log")

    host_log_file = dynamic_dir / "container-logs.log"
    host_log_file.parent.mkdir(parents=True, exist_ok=True)
    if not host_log_file.exists():
        host_log_file.touch(mode=0o666)
    try:
        host_log_file.chmod(0o666)
    except Exception:
        pass

    config = {
        "receivers": {
            "filelog": {
                "include": [container_log_path],
                "start_at": "beginning",
                "include_file_path": True,
                "include_file_name": True,
                "operators": [
                    {
                        "type": "json_parser",
                        "id": "parser-json",
                        "parse_from": "body",
                        "parse_to": "attributes"
                    }
                ]
            }
        },
        "processors": {
            "batch": {
                "timeout": "10s",
                "send_batch_size": 100
            },
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": "logs-pipeline", "action": "upsert"}
                ]
            }
        },
        "exporters": {
            "loki": {
                "endpoint": loki_push_url
            },
            "logging": {
                "loglevel": "debug"
            }
        },
        "service": {
            "pipelines": {
                "logs": {
                    "receivers": ["filelog"],
                    "processors": ["resource", "batch"],
                    "exporters": ["loki", "logging"]
                }
            },
            "telemetry": {"logs": {"level": "info"}}
        }
    }

    try:
        with config_file.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(config, fh, default_flow_style=False, sort_keys=False)
        logger.info("generate_config_logs_success file=%s", config_file)
        return {
            "success": True,
            "data": {"config_path": str(config_file), "container_log_path": container_log_path},
            "error": None
        }
    except Exception as e:
        logger.exception("generate_config_logs_failed error=%s", e)
        return {"success": False, "data": None, "error": "generate_failed"}