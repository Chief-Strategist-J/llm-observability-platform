import logging
import os
from pathlib import Path
from typing import Dict, Any
from temporalio import activity
import yaml

logger = logging.getLogger(__name__)

@activity.defn
async def generate_config_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("generate_config_logs started with params: %s", params)

    dynamic_dir = Path(params.get("dynamic_dir", "/etc/otelcol/generated"))
    dynamic_dir.mkdir(parents=True, exist_ok=True)

    config_file = dynamic_dir / "otel-collector-generated.yaml"
    
    # OTel container talks directly to Loki container (container-to-container)
    # Not through Traefik (that's only for external/Python access)
    loki_push_url = params.get("loki_push_url", "http://loki-instance-0:3100/loki/api/v1/push")
    
    # Internal container network URL (used by OTel Collector)
    # External: http://loki-instance-0:3100/loki/api/v1/push (via Traefik: http://scaibu.loki)
    # Internal: http://loki-instance-0:3100/loki/api/v1/push (direct container access)
    internal_loki_url = "http://loki-instance-0:3100/loki/api/v1/push"
    
    logger.info("Using internal Loki URL for OTel: %s", internal_loki_url)
    
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
                "endpoint": internal_loki_url  # Use internal container URL
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
        logger.info("generate_config_logs wrote config to %s", config_file)
        return {
            "success": True,
            "data": {"config_path": str(config_file), "container_log_path": container_log_path},
            "error": None
        }
    except Exception as e:
        logger.exception("generate_config_logs failed: %s", e)
        return {"success": False, "data": None, "error": "generate_failed"}