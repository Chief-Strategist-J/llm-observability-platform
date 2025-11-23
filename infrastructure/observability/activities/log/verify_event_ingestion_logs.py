import logging
import time
from typing import Dict, Any, List
from temporalio import activity
import urllib.request
import urllib.error
import urllib.parse
import json

logger = logging.getLogger(__name__)

def _build_ready_url(loki_query_url: str) -> str:
    try:
        idx = loki_query_url.find("/loki")
        if idx != -1:
            base = loki_query_url[:idx]
            return base.rstrip("/") + "/ready"
    except Exception:
        pass
    if loki_query_url.endswith("/query"):
        return loki_query_url[: -len("/query")] + "/ready"
    if loki_query_url.endswith("/query_range"):
        return loki_query_url[: -len("/query_range")] + "/ready"
    return loki_query_url.rstrip("/") + "/ready"

@activity.defn
async def verify_event_ingestion_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("verify_event_ingestion_logs started with params: %s", params)

    logql = params.get("logql", "")
    loki_query_url = params.get("loki_query_url", "http://loki.local/loki/api/v1/query")
    poll_interval = float(params.get("poll_interval", 2.0))
    timeout_seconds = int(params.get("timeout_seconds", 60))

    if not loki_query_url:
        logger.error("verify_event_ingestion_logs missing_loki_query_url")
        return {"success": False, "data": None, "error": "missing_loki_query_url"}

    if not logql:
        logger.error("verify_event_ingestion_logs missing_logql")
        return {"success": False, "data": None, "error": "missing_logql"}

    if loki_query_url.endswith("/query"):
        loki_query_url = loki_query_url[: -len("/query")] + "/query_range"
        logger.info("verify_event_ingestion_logs adjusted url to query_range: %s", loki_query_url)

    ready_url = _build_ready_url(loki_query_url)
    logger.info("verify_event_ingestion_logs waiting for loki ready at: %s", ready_url)

    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            req = urllib.request.Request(ready_url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.getcode() == 200:
                    logger.info("verify_event_ingestion_logs loki is ready")
                    break
        except Exception as e:
            logger.debug("verify_event_ingestion_logs ready check failed (will retry): %s", e)
        time.sleep(1)
    else:
        logger.error("verify_event_ingestion_logs loki_not_ready timeout after %s seconds", timeout_seconds)
        return {"success": False, "data": None, "error": "loki_not_ready"}

    q_start = time.time()
    tried_urls: List[str] = []
    attempt = 0

    while time.time() - q_start < timeout_seconds:
        attempt += 1
        try:
            query = urllib.parse.quote(logql, safe="")
            end_ns = int(time.time() * 1e9)
            start_ns = end_ns - int(10 * 60 * 1e9)

            if "?" in loki_query_url:
                full = (
                    f"{loki_query_url}&query={query}"
                    f"&start={start_ns}&end={end_ns}"
                    f"&direction=BACKWARD&limit=5000"
                )
            else:
                full = (
                    f"{loki_query_url}?query={query}"
                    f"&start={start_ns}&end={end_ns}"
                    f"&direction=BACKWARD&limit=5000"
                )

            tried_urls.append(full)
            logger.info("verify_event_ingestion_logs attempt=%d query_url=%s", attempt, full)

            req = urllib.request.Request(full, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                code = resp.getcode()
                if code == 200 and body:
                    try:
                        result = json.loads(body)
                        data = result.get("data", {})
                        results = data.get("result", [])
                        if results:
                            logger.info("verify_event_ingestion_logs SUCCESS matched results_count=%d", len(results))
                            return {
                                "success": True,
                                "data": {
                                    "url": full,
                                    "response": body,
                                    "results_count": len(results),
                                    "attempts": attempt,
                                },
                                "error": None,
                            }
                        else:
                            logger.debug("verify_event_ingestion_logs attempt=%d no_results_yet", attempt)
                    except json.JSONDecodeError:
                        logger.warning("verify_event_ingestion_logs json decode failed on attempt %d", attempt)

        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                body = ""
            logger.debug("verify_event_ingestion_logs http error %s body=%s", getattr(e, "code", None), body)

        except Exception as e:
            logger.debug("verify_event_ingestion_logs general error: %s", e)

        time.sleep(poll_interval)

    logger.error("verify_event_ingestion_logs TIMEOUT after %d attempts", attempt)
    return {
        "success": False,
        "data": {"tried_urls": tried_urls[:5], "attempts": attempt, "total_time": time.time() - q_start},
        "error": "timeout_or_no_match",
    }
