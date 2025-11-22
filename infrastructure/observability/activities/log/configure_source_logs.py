# infrastructure/observability/activities/log/configure_source_logs.py

import logging
from pathlib import Path
from typing import Dict, Any
from temporalio import activity
import shutil

logger = logging.getLogger(__name__)

@activity.defn
async def configure_source_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("configure_source_logs started with params: %s", params)
    config_path = params.get("config_path")
    dynamic_dir = Path(params.get("dynamic_dir", "/home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/dynamicconfig"))
    target_name = params.get("target_name", "base.yaml")
    if not config_path:
        logger.error("missing_config_path")
        return {"success": False, "data": None, "error": "missing_config_path"}
    try:
        dynamic_dir.mkdir(parents=True, exist_ok=True)
        target = dynamic_dir / target_name
        shutil.copyfile(config_path, target)
        logger.info("configure_source_logs copied config to %s", str(target))
        return {"success": True, "data": {"applied_config": str(target)}, "error": None}
    except Exception as e:
        logger.error("configure_source_logs failed: %s", str(e))
        return {"success": False, "data": None, "error": "apply_failed"}
