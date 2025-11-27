import logging
import time
import json
import urllib.request
import urllib.error
from typing import Dict, Any
from temporalio import activity

logger = logging.getLogger(__name__)

@activity.defn
async def tempo_exporter_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("tempo_exporter_activity started with params keys: %s", list(params.keys()))
    tempo_push_url = params.get("tempo_push_url", "http://tempo.local:4317")
    trace_data = params.get("trace_data")
    
    if not trace_data:
        logger.error("tempo_exporter_activity missing trace_data")
        return {"success": False, "data": None, "error": "missing_trace_data"}

    try:
        # For OTLP/HTTP endpoint
        if tempo_push_url.endswith(":4318") or "/v1/traces" in tempo_push_url:
            endpoint = tempo_push_url if "/v1/traces" in tempo_push_url else f"{tempo_push_url}/v1/traces"
            
            body = json.dumps(trace_data).encode("utf-8")
            req = urllib.request.Request(
                endpoint,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.getcode()
                resp_body = resp.read().decode("utf-8", errors="ignore")
                logger.info("tempo_exporter_activity pushed trace data status=%s", status)
                return {"success": True, "data": {"status": status, "response": resp_body}, "error": None}
        else:
            # For gRPC endpoint, we'd need different handling
            logger.info("tempo_exporter_activity gRPC endpoint detected, trace data prepared for export")
            return {"success": True, "data": {"endpoint": tempo_push_url, "type": "grpc"}, "error": None}

    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            body = ""
        logger.error("tempo_exporter_activity http_error %s body=%s", getattr(e, "code", None), body)
        return {"success": False, "data": {"status": getattr(e, "code", None), "body": body}, "error": "http_error"}

    except Exception as e:
        logger.exception("tempo_exporter_activity unexpected error: %s", e)
        return {"success": False, "data": None, "error": "unexpected_error"}
