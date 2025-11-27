import logging
from typing import Dict, Any, List
from temporalio import activity

logger = logging.getLogger(__name__)

@activity.defn
async def otlp_provider_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Provide OTLP trace collection endpoints and configuration
    """
    logger.info("otlp_provider_activity started with params: %s", params)
    
    grpc_endpoint = params.get("grpc_endpoint", "0.0.0.0:4317")
    http_endpoint = params.get("http_endpoint", "0.0.0.0:4318")
    enable_grpc = params.get("enable_grpc", True)
    enable_http = params.get("enable_http", True)

    try:
        endpoints: List[Dict[str, str]] = []
        
        if enable_grpc:
            endpoints.append({
                "protocol": "grpc",
                "endpoint": grpc_endpoint,
                "type": "otlp"
            })
        
        if enable_http:
            endpoints.append({
                "protocol": "http",
                "endpoint": http_endpoint,
                "type": "otlp"
            })

        logger.info("otlp_provider_activity configured %d endpoints", len(endpoints))
        
        return {
            "success": True, 
            "data": {
                "endpoints": endpoints,
                "grpc_enabled": enable_grpc,
                "http_enabled": enable_http
            }, 
            "error": None
        }
        
    except Exception as e:
        logger.exception("otlp_provider_activity error: %s", e)
        return {"success": False, "data": None, "error": "provider_failed"}
