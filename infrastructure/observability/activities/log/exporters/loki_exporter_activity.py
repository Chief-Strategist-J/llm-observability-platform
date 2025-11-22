# infrastructure/observability/activities/log/exporters/loki_exporter_activity.py
import json
import logging
import urllib.request
import urllib.error
from typing import Any, Dict
from temporalio import activity

logger = logging.getLogger(__name__)

@activity.defn
async def loki_exporter_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("loki_exporter_activity started with params: %s", params)
    url = params.get("loki_url")
    streams = params.get("streams")
    timeout = params.get("timeout_seconds", 10)
    if not url:
        logger.error("missing_loki_url")
        return {"success": False, "data": None, "error": "missing_loki_url"}
    if not streams or not isinstance(streams, list):
        logger.error("missing_or_invalid_streams")
        return {"success": False, "data": None, "error": "missing_or_invalid_streams"}
    payload = {"streams": []}
    for s in streams:
        labels = s.get("labels")
        entries = s.get("entries")
        if not labels or not entries:
            logger.error("stream_missing_labels_or_entries: %s", s)
            return {"success": False, "data": None, "error": "stream_missing_labels_or_entries"}
        payload["streams"].append({"stream": labels, "values": entries})
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url.rstrip("/") + "/loki/api/v1/push", data=body, headers={"Content-Type": "application/json"})
    try:
        logger.info("sending logs to loki at %s", url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp_body = resp.read().decode("utf-8")
            logger.info("loki_exporter_activity success: status=%s", resp.status)
            return {"success": True, "data": {"status": resp.status, "body": resp_body}, "error": None}
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            err_body = ""
        logger.error("loki_exporter_activity http_error: code=%s body=%s", e.code, err_body)
        return {"success": False, "data": {"status": getattr(e, "code", None), "body": err_body}, "error": "http_error"}
    except Exception as e:
        logger.error("loki_exporter_activity error: %s", str(e))
        return {"success": False, "data": None, "error": "network_or_unknown_error"}
