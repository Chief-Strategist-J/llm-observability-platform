import logging
from typing import Dict, Any
from temporalio import activity

logger = logging.getLogger(__name__)

@activity.defn
async def span_processor_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.debug("Entered span_processor_activity with raw params: %s", params)

    span_data = params.get("span_data")
    logger.debug("Span data presence: %s", "present" if span_data is not None else "missing")

    if span_data is None:
        logger.error("span_processor_activity missing span_data")
        return {"success": False, "data": None, "error": "missing_span_data"}
    
    try:
        processed_span = span_data.copy() if isinstance(span_data, dict) else {}
        logger.debug("Initial processed_span created: %s", processed_span)

        if "attributes" not in processed_span:
            processed_span["attributes"] = {}
            logger.debug("Attributes field created in processed_span")

        processed_span["attributes"]["processor.name"] = "span_processor"
        processed_span["attributes"]["processed"] = True

        logger.debug("span_processor_activity updated span attributes: %s", processed_span.get("attributes"))
        return {"success": True, "data": {"processed_span": processed_span}, "error": None}
        
    except Exception as e:
        logger.debug("Unexpected exception type: %s", type(e))
        logger.exception("span_processor_activity error: %s", e)
        return {"success": False, "data": None, "error": "process_error"}
