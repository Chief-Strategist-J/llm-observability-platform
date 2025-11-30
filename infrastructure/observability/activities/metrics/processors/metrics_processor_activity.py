import logging
from typing import Dict, Any, List
from temporalio import activity

logger = logging.getLogger(__name__)

@activity.defn
async def metrics_processor_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process and transform metrics data (filtering, aggregation, enrichment).
    
    Args:
        params: Dictionary containing:
            - metrics_data: Metrics data to process (dict or list of dicts)
            - filters: Optional filters to apply
            - aggregations: Optional aggregations to perform
            
    Returns:
        Dictionary with success status, processed metrics, and error info
    """
    logger.debug("Entered metrics_processor_activity with raw params: %s", params)

    metrics_data = params.get("metrics_data")
    logger.debug("Metrics data presence: %s", "present" if metrics_data is not None else "missing")

    if metrics_data is None:
        logger.error("metrics_processor_activity missing metrics_data")
        return {"success": False, "data": None, "error": "missing_metrics_data"}
    
    try:
        # Normalize to list
        if isinstance(metrics_data, dict):
            metrics_list = [metrics_data]
        elif isinstance(metrics_data, list):
            metrics_list = metrics_data
        else:
            metrics_list = []
            
        logger.debug("Normalized metrics list length: %d", len(metrics_list))

        processed_metrics = []
        filters = params.get("filters", {})
        
        for metric in metrics_list:
            if not isinstance(metric, dict):
                continue
                
            processed_metric = metric.copy()
            logger.debug("Processing metric: %s", metric.get("name", "unnamed"))

            # Add processor metadata
            if "metadata" not in processed_metric:
                processed_metric["metadata"] = {}
                logger.debug("Metadata field created in processed_metric")

            processed_metric["metadata"]["processor.name"] = "metrics_processor"
            processed_metric["metadata"]["processed"] = True
            
            # Apply filters if specified
            if filters:
                should_include = True
                for filter_key, filter_value in filters.items():
                    if processed_metric.get(filter_key) != filter_value:
                        should_include = False
                        break
                if not should_include:
                    logger.debug("Filtered out metric: %s", metric.get("name"))
                    continue

            processed_metrics.append(processed_metric)

        logger.debug("metrics_processor_activity processed %d metrics", len(processed_metrics))
        return {
            "success": True, 
            "data": {"processed_metrics": processed_metrics, "count": len(processed_metrics)}, 
            "error": None
        }
        
    except Exception as e:
        logger.debug("Unexpected exception type: %s", type(e))
        logger.exception("metrics_processor_activity error: %s", e)
        return {"success": False, "data": None, "error": "process_error"}
