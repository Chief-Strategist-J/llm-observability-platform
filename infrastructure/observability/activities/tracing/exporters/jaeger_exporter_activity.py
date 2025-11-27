import logging
import json
import urllib.request
import urllib.error
from typing import Dict, Any
from temporalio import activity

logger = logging.getLogger(__name__)

@activity.defn
async def jaeger_exporter_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.debug("Entered jaeger_exporter_activity with raw params: %s", params)
    logger.info("jaeger_exporter_activity started with params keys: %s", list(params.keys()))

    jaeger_endpoint = params.get("jaeger_endpoint", "http://jaeger.local:14268/api/traces")
    logger.debug("Resolved jaeger_endpoint: %s", jaeger_endpoint)

    trace_data = params.get("trace_data")
    logger.debug("Trace data presence check: %s", "present" if trace_data else "missing")

    if not trace_data:
        logger.error("jaeger_exporter_activity missing trace_data")
        return {"success": False, "data": None, "error": "missing_trace_data"}

    try:
        body = json.dumps(trace_data).encode("utf-8")
        logger.debug("Serialized trace_data into JSON with length: %d bytes", len(body))

        req = urllib.request.Request(
            jaeger_endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        logger.debug("Prepared HTTP request to Jaeger endpoint")

        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.getcode()
            logger.debug("HTTP response status received: %s", status)

            resp_body = resp.read().decode("utf-8", errors="ignore")
            logger.debug("HTTP response body length: %d chars", len(resp_body))

            logger.info("jaeger_exporter_activity pushed trace data status=%s", status)
            return {"success": True, "data": {"status": status, "response": resp_body}, "error": None}

    except urllib.error.HTTPError as e:
        logger.debug("HTTPError caught in jaeger_exporter_activity: %s", e)
        try:
            body = e.read().decode("utf-8", errors="ignore")
            logger.debug("Extracted HTTPError body with length: %d chars", len(body))
        except Exception:
            body = ""
            logger.debug("Failed to read body from HTTPError; using empty string")

        logger.error("jaeger_exporter_activity http_error %s body=%s", getattr(e, "code", None), body)
        return {"success": False, "data": {"status": getattr(e, "code", None), "body": body}, "error": "http_error"}

    except Exception as e:
        logger.debug("Unexpected exception type: %s", type(e))
        logger.exception("jaeger_exporter_activity unexpected error: %s", e)
        return {"success": False, "data": None, "error": "unexpected_error"}
