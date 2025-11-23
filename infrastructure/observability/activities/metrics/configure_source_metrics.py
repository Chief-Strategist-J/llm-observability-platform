import logging
from pathlib import Path
from typing import Dict, Any
from temporalio import activity
import shutil

logger = logging.getLogger(__name__)

@activity.defn
async def configure_source_metrics(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("configure_source_metrics_start params=%s", list(params.keys()))

    config_path = params.get("config_path")
    if not config_path:
        logger.error("configure_source_metrics_missing_config_path")
        return {"success": False, "data": None, "error": "missing_config_path"}

    dynamic_dir = Path(params.get(
        "dynamic_dir",
        "/home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/dynamicconfig"
    ))
    target_name = params.get("target_name", "otel-metrics.yaml")

    logger.debug("configure_source_metrics_params config=%s target=%s", config_path, target_name)

    try:
        src = Path(config_path).expanduser()
        if not src.exists() or not src.is_file():
            logger.error("configure_source_metrics_source_not_found path=%s", src)
            return {"success": False, "data": None, "error": "source_not_found"}

        dynamic_dir.mkdir(parents=True, exist_ok=True)
        target = (dynamic_dir / target_name).resolve()

        logger.debug("configure_source_metrics_copy from=%s to=%s", src, target)

        try:
            if src.resolve() == target:
                logger.info("configure_source_metrics_same_file path=%s", target)
            else:
                shutil.copy2(str(src), str(target))
                logger.info("configure_source_metrics_copied from=%s to=%s", src, target)
        except Exception:
            shutil.copyfile(str(src), str(target))
            logger.info("configure_source_metrics_fallback_copy from=%s to=%s", src, target)

        try:
            target.chmod(0o644)
        except Exception as e:
            logger.debug("configure_source_metrics_chmod_warning error=%s", e)

        if not target.exists():
            logger.error("configure_source_metrics_copy_failed target=%s", target)
            return {"success": False, "data": None, "error": "copy_failed"}

        size = target.stat().st_size
        logger.info("configure_source_metrics_success target=%s size=%s", target, size)

        return {"success": True, "data": {"applied_config": str(target), "size": size}, "error": None}

    except Exception as e:
        logger.exception("configure_source_metrics_failed error=%s", e)
        return {"success": False, "data": None, "error": "apply_failed"}