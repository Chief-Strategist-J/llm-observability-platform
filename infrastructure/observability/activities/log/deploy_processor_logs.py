import logging
from pathlib import Path
from typing import Dict, Any
from temporalio import activity
import yaml

logger = logging.getLogger(__name__)

@activity.defn
async def deploy_processor_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("deploy_processor_logs started with params: %s", params)
    dynamic_dir = Path(params.get("dynamic_dir", "/etc/otelcol/generated"))
    config_name = params.get("config_name", "otel-collector-generated.yaml")
    try:
        cfg_file = dynamic_dir / config_name
        if not cfg_file.exists():
            logger.error("config_not_found: %s", str(cfg_file))
            return {"success": False, "data": None, "error": "config_not_found"}

        text = cfg_file.read_text(encoding="utf-8")
        try:
            cfg = yaml.safe_load(text) or {}
        except Exception:
            cfg = {}

        processors_deployed = bool(cfg.get("processors"))
        logger.info("deploy_processor_logs processors_present=%s", processors_deployed)
        return {
            "success": True,
            "data": {"processors_present": processors_deployed, "config_path": str(cfg_file)},
            "error": None
        }
    except Exception as e:
        logger.exception("deploy_processor_logs failed: %s", e)
        return {"success": False, "data": None, "error": "deploy_failed"}
