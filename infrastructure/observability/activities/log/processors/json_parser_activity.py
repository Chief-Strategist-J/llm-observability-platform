import logging
import json
from typing import Dict, Any
from temporalio import activity

logger = logging.getLogger(__name__)

@activity.defn
async def json_parser_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    line = params.get("line")
    if line is None:
        logger.error("json_parser_activity missing line")
        return {"success": False, "data": None, "error": "missing_line"}
    try:
        parsed = json.loads(line)
        logger.debug("json_parser_activity parsed keys=%s", list(parsed.keys()) if isinstance(parsed, dict) else None)
        return {"success": True, "data": {"parsed": parsed}, "error": None}
    except json.JSONDecodeError:
        logger.debug("json_parser_activity not json, returning raw")
        return {"success": True, "data": {"parsed": {"raw": line}}, "error": None}
    except Exception as e:
        logger.exception("json_parser_activity error: %s", e)
        return {"success": False, "data": None, "error": "parse_error"}
