import logging
from pathlib import Path
from typing import Dict, Any
from temporalio import activity
import shutil

logger = logging.getLogger(__name__)

@activity.defn
async def configure_source_tracings(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.debug("Entered configure_source_tracings with raw params: %s", params)
    logger.info("configure_source_tracings started with params: %s", params)

    config_path = params.get("config_path")
    logger.debug("Resolved config_path: %s", config_path)

    if not config_path:
        logger.error("configure_source_tracings: missing_config_path")
        return {"success": False, "data": None, "error": "missing_config_path"}

    dynamic_dir = Path(params.get(
        "dynamic_dir",
        "/home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/dynamicconfig"
    ))
    target_name = params.get("target_name", "base.yaml")

    logger.debug("Resolved dynamic_dir: %s", dynamic_dir)
    logger.debug("Resolved target_name: %s", target_name)

    try:
        src = Path(config_path).expanduser()
        logger.debug("Expanded source path: %s", src)

        if not src.exists() or not src.is_file():
            logger.error("configure_source_tracings: source config not found: %s", str(src))
            return {"success": False, "data": None, "error": "source_not_found"}

        dynamic_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("Ensured dynamic_dir exists: %s", dynamic_dir)

        target = (dynamic_dir / target_name).resolve()
        logger.debug("Resolved target path: %s", target)

        try:
            if src.resolve() == target:
                logger.info("configure_source_tracings: source and target are the same file (%s). No copy needed.", str(target))
            else:
                logger.debug("Attempting primary copy (copy2) from %s to %s", src, target)
                shutil.copy2(str(src), str(target))
                logger.info("configure_source_tracings copied config from %s to %s", str(src), str(target))
        except Exception as e:
            logger.debug("Primary copy failed (%s). Falling back to copyfile.", e)
            shutil.copyfile(str(src), str(target))
            logger.info("configure_source_tracings fallback copyfile used for %s -> %s", str(src), str(target))

        try:
            logger.debug("Attempting chmod 644 on %s", target)
            target.chmod(0o644)
        except Exception as e:
            logger.debug("configure_source_tracings chmod warning: %s", e)

        if not target.exists():
            logger.error("configure_source_tracings failed: target not present after copy: %s", str(target))
            return {"success": False, "data": None, "error": "copy_failed"}

        size = target.stat().st_size
        logger.debug("Computed target file size: %d bytes", size)

        logger.info("configure_source_tracings success target=%s size=%d", str(target), size)

        return {"success": True, "data": {"applied_config": str(target), "size": size}, "error": None}

    except Exception as e:
        logger.debug("Unexpected exception type: %s", type(e))
        logger.exception("configure_source_tracings failed: %s", e)
        return {"success": False, "data": None, "error": "apply_failed"}
