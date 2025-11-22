# infrastructure/observability/activities/log/processors/json_parser_activity.py
import json
import logging
from typing import Any, Dict, List, Union
from temporalio import activity

logger = logging.getLogger(__name__)

@activity.defn
async def json_parser_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("json_parser_activity started with params: %s", params)
    single = params.get("log")
    many = params.get("logs")
    if single is None and many is None:
        logger.error("missing_input")
        return {"success": False, "data": None, "error": "missing_input"}
    def parse_item(item: Union[str, bytes]) -> Dict[str, Any]:
        if isinstance(item, bytes):
            item = item.decode("utf-8", errors="ignore")
        if not isinstance(item, str):
            raise ValueError("item_not_string")
        return json.loads(item)
    try:
        if single is not None:
            logger.info("parsing single log")
            parsed = parse_item(single)
            logger.info("json_parser_activity parsed_single_success")
            return {"success": True, "data": parsed, "error": None}
        logger.info("parsing multiple logs: count=%s", len(many))
        if not isinstance(many, list):
            logger.error("logs_must_be_list")
            return {"success": False, "data": None, "error": "logs_must_be_list"}
        parsed_list: List[Dict[str, Any]] = []
        for it in many:
            parsed_list.append(parse_item(it))
        logger.info("json_parser_activity parsed_many_success: count=%s", len(parsed_list))
        return {"success": True, "data": parsed_list, "error": None}
    except json.JSONDecodeError as e:
        logger.error("json_decode_error: %s", str(e))
        return {"success": False, "data": None, "error": "json_decode_error"}
    except Exception as e:
        logger.error("unexpected_error: %s", str(e))
        return {"success": False, "data": None, "error": "unexpected_error"}
