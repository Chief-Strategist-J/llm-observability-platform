# infrastructure/observability/activities/log/verify_event_ingestion_logs.py
import logging
import time
from typing import Dict, Any, List
from temporalio import activity
import urllib.request
import urllib.error
import urllib.parse

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
    return loki_query_url.rstrip("/") + "/ready"

@activity.defn
async def verify_event_ingestion_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("verify_event_ingestion_logs started with params: %s", params)
    logql = params.get("logql", "")
    loki_query_url = params.get("loki_query_url")
    poll_interval = float(params.get("poll_interval", 2.0))
    timeout_seconds = int(params.get("timeout_seconds", 60))
    if not loki_query_url:
        logger.error("missing_loki_query_url")
        return {"success": False, "data": None, "error": "missing_loki_query_url"}
    if not logql:
        logger.error("missing_logql")
        return {"success": False, "data": None, "error": "missing_logql"}
    ready_url = _build_ready_url(loki_query_url)
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            req = urllib.request.Request(ready_url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                code = resp.getcode()
                if code == 200:
                    break
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                body = ""
            logger.info("loki_ready_http_error code=%s body=%s", getattr(e, "code", None), body)
        except Exception as e:
            logger.info("loki_ready_error: %s", str(e))
        time.sleep(1)
    else:
        logger.error("loki_not_ready timeout")
        return {"success": False, "data": None, "error": "loki_not_ready"}
    q_start = time.time()
    tried_urls: List[str] = []
    while time.time() - q_start < timeout_seconds:
        try:
            query = urllib.parse.quote(logql, safe="")
            url = loki_query_url
            if "?" in url:
                full = f"{url}&query={query}"
            else:
                full = f"{url}?query={query}"
            tried_urls.append(full)
            req = urllib.request.Request(full, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                code = resp.getcode()
                if code == 200 and body:
                    logger.info("verify_event_ingestion_logs matched: url=%s", full)
                    return {"success": True, "data": {"url": full, "response": body}, "error": None}
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                body = ""
            logger.info("loki_query_http_error: code=%s body=%s", getattr(e, "code", None), body)
        except Exception as e:
            last_err = e
            logger.info("loki_url_error: %s", str(e))
        time.sleep(poll_interval)
    logger.error("verify_event_ingestion_logs timeout last_error=%s tried_urls=%s", locals().get("last_err", "none"), tried_urls)
    return {"success": False, "data": {"tried_urls": tried_urls}, "error": "timeout_or_no_match"}
