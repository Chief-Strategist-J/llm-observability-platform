import logging
from pathlib import Path
from typing import Dict, Any
from temporalio import activity
import yaml
from infrastructure.observability.config.constants import OBSERVABILITY_CONFIG

logger = logging.getLogger(__name__)

@activity.defn
async def generate_config_tracings(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("generate_config_tracings_start params_keys=%s", list(params.keys()))

    dynamic_dir = Path(params.get("dynamic_dir", "/etc/otelcol/generated"))
    dynamic_dir.mkdir(parents=True, exist_ok=True)
    logger.debug("generate_config_tracings_dir dir=%s", dynamic_dir)

    config_file = dynamic_dir / "otel-collector-tracings-generated.yaml"
    logger.debug("generate_config_tracings_file file=%s", config_file)

    tempo_push_url = params.get("tempo_push_url", OBSERVABILITY_CONFIG.TEMPO_URL)
    internal_tempo_url = params.get("internal_tempo_url", OBSERVABILITY_CONFIG.TEMPO_GRPC_URL)

    logger.info("generate_config_tracings_tempo internal_url=%s external_url=%s",
                internal_tempo_url, tempo_push_url)

    otlp_grpc_endpoint = params.get("otlp_grpc_endpoint", "0.0.0.0:4317")
    otlp_http_endpoint = params.get("otlp_http_endpoint", "0.0.0.0:4318")

    logger.debug("generate_config_tracings_otlp grpc=%s http=%s",
                 otlp_grpc_endpoint, otlp_http_endpoint)

    config = {
        "receivers": {
            "otlp": {
                "protocols": {
                    "grpc": {"endpoint": otlp_grpc_endpoint},
                    "http": {"endpoint": otlp_http_endpoint}
                }
            }
        },
        "processors": {
            "batch": {"timeout": "10s", "send_batch_size": 100},
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": "traces-pipeline", "action": "upsert"}
                ]
            }
        },
        "exporters": {
            "otlp": {
                "endpoint": internal_tempo_url,
                "tls": {"insecure": True}
            },
            "logging": {"loglevel": "debug"}
        },
        "service": {
            "pipelines": {
                "traces": {
                    "receivers": ["otlp"],
                    "processors": ["resource", "batch"],
                    "exporters": ["otlp", "logging"]
                }
            },
            "telemetry": {"logs": {"level": "info"}}
        }
    }

    try:
        with config_file.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(config, fh, default_flow_style=False, sort_keys=False)

        logger.info("generate_config_tracings_success file=%s grpc=%s http=%s",
                    config_file, otlp_grpc_endpoint, otlp_http_endpoint)

        return {
            "success": True,
            "data": {
                "config_path": str(config_file),
                "otlp_grpc_endpoint": otlp_grpc_endpoint,
                "otlp_http_endpoint": otlp_http_endpoint
            },
            "error": None
        }

    except Exception as e:
        logger.exception("generate_config_tracings_failed error=%s", e)
        return {"success": False, "data": None, "error": "generate_failed"}