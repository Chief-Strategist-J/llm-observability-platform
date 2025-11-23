import logging
from pathlib import Path
import yaml
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

    log_file = dynamic_dir / "container-logs.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.touch(exist_ok=True)
    
    try:
        log_file.chmod(0o666)
    except Exception as e:
<<<<<<< HEAD
        logger.warning("generate_config_logs chmod warning: %s", e)
    
    logger.info("generate_config_logs log_file=%s exists=%s", log_file, log_file.exists())
    
=======
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

>>>>>>> dcbfd98fbef16d9d913e8e94ea82905b860c2c85
    config = {
        "receivers": {
            "filelog": {
                "include": [str(log_file.absolute())],
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
                    {
                        "key": "service.name",
                        "value": "logs-pipeline",
                        "action": "upsert"
                    }
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
            "telemetry": {
                "logs": {
                    "level": "debug"
                }
            }
        }
    }

    try:
        with config_file.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(config, fh, default_flow_style=False, sort_keys=False)
        
        logger.info("generate_config_logs wrote config: %s", str(config_file))
        
        verify_text = config_file.read_text(encoding="utf-8")
        logger.info("generate_config_logs config_size=%d config_preview=%s", len(verify_text), verify_text[:200])
        
        return {
            "success": True,
            "data": {"config_path": str(config_file), "log_file": str(log_file)},
            "error": None
        }
    except Exception as e:
        logger.error("generate_config_logs failed: %s", str(e))
        return {"success": False, "data": None, "error": "generate_failed"}