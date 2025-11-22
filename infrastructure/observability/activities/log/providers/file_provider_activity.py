# infrastructure/observability/activities/log/providers/file_provider_activity.py
import logging
from pathlib import Path
from typing import Any, Dict, List
from temporalio import activity

logger = logging.getLogger(__name__)

@activity.defn
async def file_provider_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("file_provider_activity started with params: %s", params)
    paths = params.get("paths")
    tail_lines = params.get("tail_lines", 100)
    if not paths or not isinstance(paths, list):
        logger.error("missing_or_invalid_paths")
        return {"success": False, "data": None, "error": "missing_or_invalid_paths"}
    result: Dict[str, List[str]] = {}
    for p in paths:
        logger.info("reading_file: %s", p)
        try:
            path = Path(p)
            if not path.exists() or not path.is_file():
                logger.warning("file_not_found_or_invalid: %s", p)
                result[p] = []
                continue
            with path.open("rb") as fh:
                fh.seek(0, 2)
                file_size = fh.tell()
                block_size = 1024
                data = b""
                lines_found = 0
                pointer = file_size
                while pointer > 0 and lines_found <= tail_lines:
                    read_size = min(block_size, pointer)
                    pointer -= read_size
                    fh.seek(pointer)
                    chunk = fh.read(read_size)
                    data = chunk + data
                    lines_found = data.count(b"\n")
                text = data.decode("utf-8", errors="replace")
                lines = text.splitlines()[-tail_lines:]
                result[p] = lines
                logger.info("file_provider_activity read_success: %s lines=%s", p, len(lines))
        except Exception as e:
            logger.error("file_provider_activity error for %s: %s", p, str(e))
            result[p] = []
    logger.info("file_provider_activity finished")
    return {"success": True, "data": result, "error": None}
