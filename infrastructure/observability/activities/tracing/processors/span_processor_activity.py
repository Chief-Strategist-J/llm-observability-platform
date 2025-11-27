import logging
from typing import Dict, Any
from temporalio import activity

logger = logging.getLogger(__name__)

@activity.defn
async def span_processor_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process span data by adding attributes, filtering, or transforming spans
    """
    span_data = params.get("span_data")
    if span_data is None:
        logger.error("span_processor_activity missing span_data")
        return {"success": False, "data": None, "error": "missing_span_data"}
    
    try:
        # Process span attributes
        processed_span = span_data.copy() if isinstance(span_data, dict) else {}
        
        # Add processor metadata
        if "attributes" not in processed_span:
            processed_span["attributes"] = {}
        
        processed_span["attributes"]["processor.name"] = "span_processor"
        processed_span["attributes"]["processed"] = True
        
        logger.debug("span_processor_activity processed span with attributes")
        return {"success": True, "data": {"processed_span": processed_span}, "error": None}
        
    except Exception as e:
        logger.exception("span_processor_activity error: %s", e)
        return {"success": False, "data": None, "error": "process_error"}
