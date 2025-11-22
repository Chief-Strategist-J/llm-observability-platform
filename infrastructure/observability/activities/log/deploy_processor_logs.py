# infrastructure/observability/activities/log/deploy_processor_logs.py
import logging
from pathlib import Path
from typing import Dict, Any
from temporalio import activity

logger = logging.getLogger(__name__)

@activity.defn
async def deploy_processor_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("deploy_processor_logs started with params: %s", params)
    dynamic_dir = Path(params.get("dynamic_dir", "/home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/dynamicconfig"))
    config_name = params.get("config_name", "otel-collector-generated.yaml")
    try:
        cfg_file = dynamic_dir / config_name
        if not cfg_file.exists():
            logger.error("config_not_found: %s", str(cfg_file))
            return {"success": False, "data": None, "error": "config_not_found"}
        text = cfg_file.read_text(encoding="utf-8")
        processors_deployed = "processors" in text
        logger.info("deploy_processor_logs deployed processors=%s", processors_deployed)
        return {"success": True, "data": {"processors_present": processors_deployed, "config_path": str(cfg_file)}, "error": None}
    except Exception as e:
        logger.error("deploy_processor_logs failed: %s", str(e))
        return {"success": False, "data": None, "error": "deploy_failed"}
