import logging
from typing import Dict, Any, List
from temporalio import activity

logger = logging.getLogger(__name__)

@activity.defn
async def prometheus_provider_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Provide Prometheus scrape endpoints and configuration.
    
    Args:
        params: Dictionary containing:
            - scrape_endpoint: Prometheus scrape endpoint (default: 0.0.0.0:9090)
            - pushgateway_endpoint: Optional push gateway endpoint
            - scrape_interval: Scrape interval in seconds
            - enable_scrape: Enable scrape endpoint
            - enable_push: Enable push gateway
            
    Returns:
        Dictionary with success status, endpoint configuration, and error info
    """
    logger.info("prometheus_provider_activity started with params: %s", params)
    
    scrape_endpoint = params.get("scrape_endpoint", "0.0.0.0:9090")
    pushgateway_endpoint = params.get("pushgateway_endpoint", "0.0.0.0:9091")
    scrape_interval = params.get("scrape_interval", 15)
    enable_scrape = params.get("enable_scrape", True)
    enable_push = params.get("enable_push", False)

    try:
        endpoints: List[Dict[str, Any]] = []
        
        if enable_scrape:
            endpoints.append({
                "protocol": "http",
                "endpoint": scrape_endpoint,
                "type": "scrape",
                "interval": scrape_interval
            })
            logger.debug("Configured scrape endpoint: %s", scrape_endpoint)
        
        if enable_push:
            endpoints.append({
                "protocol": "http",
                "endpoint": pushgateway_endpoint,
                "type": "push_gateway"
            })
            logger.debug("Configured push gateway endpoint: %s", pushgateway_endpoint)

        logger.info("prometheus_provider_activity configured %d endpoints", len(endpoints))
        
        return {
            "success": True, 
            "data": {
                "endpoints": endpoints,
                "scrape_enabled": enable_scrape,
                "push_enabled": enable_push,
                "scrape_interval": scrape_interval
            }, 
            "error": None
        }
        
    except Exception as e:
        logger.exception("prometheus_provider_activity error: %s", e)
        return {"success": False, "data": None, "error": "provider_failed"}
