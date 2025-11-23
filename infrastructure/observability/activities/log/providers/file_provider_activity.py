import logging
import glob
from pathlib import Path
from typing import Dict, Any, List
from temporalio import activity

logger = logging.getLogger(__name__)

@activity.defn
async def file_provider_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("file_provider_activity started with params: %s", params)
    patterns = params.get("patterns") or params.get("pattern")
    if not patterns:
        logger.error("file_provider_activity missing patterns")
        return {"success": False, "data": None, "error": "missing_patterns"}
    if isinstance(patterns, str):
        patterns = [patterns]

    tail_lines = int(params.get("tail_lines", 10))
    resolved: Dict[str, List[str]] = {}

    try:
        for pat in patterns:
            matches = sorted(glob.glob(pat))
            resolved[pat] = matches

        content: Dict[str, List[str]] = {}
        for pat, files in resolved.items():
            for f in files:
                try:
                    p = Path(f)
                    if not p.exists():
                        continue
                    with p.open("r", encoding="utf-8", errors="ignore") as fh:
                        lines = fh.readlines()
                    last = [ln.rstrip("\n") for ln in lines[-tail_lines:]] if lines else []
                    content.setdefault(pat, []).append({"file": str(p.resolve()), "last_lines": last})
                except Exception as e:
                    logger.exception("file_provider_activity read error for %s: %s", f, e)

        return {"success": True, "data": {"resolved": resolved, "content": content}, "error": None}
    except Exception as e:
        logger.exception("file_provider_activity error: %s", e)
        return {"success": False, "data": None, "error": "provider_failed"}
