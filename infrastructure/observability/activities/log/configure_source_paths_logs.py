# infrastructure/observability/activities/log/configure_source_paths_logs.py
import logging
from pathlib import Path
import glob
from typing import Dict, Any, List
from temporalio import activity

logger = logging.getLogger(__name__)

@activity.defn
async def configure_source_paths_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("configure_source_paths_logs started with params: %s", params)
    config_path = params.get("config_path")
    if not config_path:
        logger.error("missing_config_path")
        return {"success": False, "data": None, "error": "missing_config_path"}
    try:
        from yaml import safe_load
        cfg = safe_load(Path(config_path).read_text(encoding="utf-8"))
        receivers = cfg.get("receivers", {})
        includes: List[str] = []
        for rcfg in receivers.values():
            filelog = rcfg.get("filelog") if isinstance(rcfg, dict) else rcfg.get("filelog")
            if not filelog:
                filelog = rcfg.get("include") if isinstance(rcfg, dict) else None
            if isinstance(filelog, dict):
                inc = filelog.get("include", [])
                if isinstance(inc, list):
                    includes.extend(inc)
            elif isinstance(rcfg, dict) and "include" in rcfg:
                inc = rcfg.get("include", [])
                if isinstance(inc, list):
                    includes.extend(inc)
        resolved: Dict[str, List[str]] = {}
        for pattern in includes:
            matches = glob.glob(pattern)
            resolved[pattern] = matches
        logger.info("configure_source_paths_logs resolved %s entries", len(resolved))
        return {"success": True, "data": {"resolved_paths": resolved}, "error": None}
    except Exception as e:
        logger.error("configure_source_paths_logs error: %s", str(e))
        return {"success": False, "data": None, "error": "path_resolution_failed"}
