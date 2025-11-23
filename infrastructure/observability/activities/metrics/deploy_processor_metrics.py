import logging
from pathlib import Path
from typing import Dict, Any
from temporalio import activity
import yaml

logger = logging.getLogger(__name__)

@activity.defn
async def deploy_processor_metrics(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("deploy_processor_metrics_start params=%s", list(params.keys()))
    dynamic_dir = Path(params.get("dynamic_dir", "/home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/dynamicconfig"))
    config_name = params.get("config_name", "otel-collector-metrics.yaml")
    
    logger.debug("deploy_processor_metrics_params dir=%s config=%s", dynamic_dir, config_name)
    
    try:
        cfg_file = dynamic_dir / config_name
        if not cfg_file.exists():
            logger.error("deploy_processor_metrics_config_not_found path=%s", cfg_file)
            return {"success": False, "data": None, "error": "config_not_found"}

        text = cfg_file.read_text(encoding="utf-8")
        try:
            cfg = yaml.safe_load(text) or {}
        except Exception as e:
            logger.error("deploy_processor_metrics_yaml_parse_failed error=%s", e)
            cfg = {}

        processors_deployed = bool(cfg.get("processors"))
        logger.info("deploy_processor_metrics_result processors_present=%s", processors_deployed)
        return {
            "success": True,
            "data": {"processors_present": processors_deployed, "config_path": str(cfg_file)},
            "error": None
        }
    except Exception as e:
        logger.exception("deploy_processor_metrics_failed error=%s", e)
        return {"success": False, "data": None, "error": "deploy_failed"}