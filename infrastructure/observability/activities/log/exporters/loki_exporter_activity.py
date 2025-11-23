import logging
import time
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List
from temporalio import activity

logger = logging.getLogger(__name__)

@activity.defn
async def loki_exporter_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("loki_exporter_activity started with params keys: %s", list(params.keys()))
    loki_push_url = params.get("loki_push_url", "http://loki.local/loki/api/v1/push")
    raw_lines = params.get("lines") or params.get("line") or []
    if isinstance(raw_lines, str):
        raw_lines = [raw_lines]
    labels = params.get("labels", {"job": "synthetic"})

    if not raw_lines:
        logger.error("loki_exporter_activity missing lines")
        return {"success": False, "data": None, "error": "missing_lines"}

    try:
        values = []
        ts_ns = str(int(time.time() * 1e9))
        for ln in raw_lines:
            values.append([ts_ns, ln if ln.endswith("\n") else ln + "\n"])

        payload = {"streams": [{"stream": labels, "values": values}]}
        body = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            loki_push_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.getcode()
            resp_body = resp.read().decode("utf-8", errors="ignore")
            logger.info("loki_exporter_activity pushed %d lines status=%s", len(values), status)
            return {"success": True, "data": {"status": status, "response": resp_body}, "error": None}

    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            body = ""
        logger.error("loki_exporter_activity http_error %s body=%s", getattr(e, "code", None), body)
        return {"success": False, "data": {"status": getattr(e, "code", None), "body": body}, "error": "http_error"}

    except Exception as e:
        logger.exception("loki_exporter_activity unexpected error: %s", e)
        return {"success": False, "data": None, "error": "unexpected_error"}
