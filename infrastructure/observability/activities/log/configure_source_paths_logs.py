import logging
from pathlib import Path
import glob
from typing import Dict, Any, List
from temporalio import activity
import yaml

logger = logging.getLogger(__name__)

@activity.defn
async def configure_source_paths_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("configure_source_paths_logs started with params: %s", params)
    config_path = params.get("config_path")
    if not config_path:
        logger.error("missing_config_path")
        return {"success": False, "data": None, "error": "missing_config_path"}

    try:
        cfg_text = Path(config_path).read_text(encoding="utf-8")
        cfg = yaml.safe_load(cfg_text) or {}
        receivers = cfg.get("receivers", {}) or {}

        includes: List[str] = []
        for rcfg in receivers.values():
            if isinstance(rcfg, dict):
                if "include" in rcfg and isinstance(rcfg.get("include"), list):
                    includes.extend(rcfg.get("include"))
                elif "filelog" in rcfg and isinstance(rcfg.get("filelog"), dict):
                    inc = rcfg["filelog"].get("include", [])
                    if isinstance(inc, list):
                        includes.extend(inc)

        resolved: Dict[str, List[str]] = {}
        for pattern in includes:
            matches = [str(Path(p).resolve()) for p in glob.glob(pattern)]
            resolved[pattern] = matches

        logger.info("configure_source_paths_logs resolved %d include patterns", len(resolved))
        return {"success": True, "data": {"resolved_paths": resolved, "includes": includes}, "error": None}
    except Exception as e:
        logger.exception("configure_source_paths_logs error: %s", e)
        return {"success": False, "data": None, "error": "path_resolution_failed"}
