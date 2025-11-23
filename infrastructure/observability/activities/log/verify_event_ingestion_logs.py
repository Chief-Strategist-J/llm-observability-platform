import logging
import time
import asyncio
import socket
from typing import Dict, Any, List
from temporalio import activity
import urllib.request
import urllib.error
import urllib.parse
import json

logger = logging.getLogger(__name__)


def _can_connect(url: str, timeout: float = 5.0) -> bool:
    """Check if we can connect to the URL"""
    try:
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            return result == 0
    except Exception as e:
        logger.debug("Connection check failed for %s: %s", url, e)
        return False


async def _wait_for_connection(url: str, retries: int = 15, delay: float = 2.0) -> bool:
    """Wait for service to be reachable"""
    for attempt in range(1, retries + 1):
        if _can_connect(url):
            logger.info("Service reachable at %s on attempt=%d", url, attempt)
            return True
        logger.warning("Service not reachable at %s attempt=%d", url, attempt)
        await asyncio.sleep(delay)
    return False


def _ensure_query_range_url(loki_query_url: str) -> str:
    parsed = urllib.parse.urlparse(loki_query_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    if parsed.path.endswith("/query_range"):
        return loki_query_url
    if parsed.path.endswith("/query"):
        return urllib.parse.urlunparse(
            (parsed.scheme, parsed.netloc,
             parsed.path[:-len("/query")] + "/query_range",
             "", parsed.query, "")
        )
    return f"{base}/loki/api/v1/query_range"


def _build_ready_url(loki_query_url: str) -> str:
    parsed = urllib.parse.urlparse(loki_query_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    return f"{base}/ready"


@activity.defn
async def verify_event_ingestion_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("verify_event_ingestion_logs started with params: %s", params)

    logql = params.get("logql")
    loki_query_url = params.get("loki_query_url")
    poll_interval = float(params.get("poll_interval", 2))
    timeout_seconds = int(params.get("timeout_seconds", 60))

    if not logql:
        return {"success": False, "data": None, "error": "missing_logql"}

    if not loki_query_url:
        return {"success": False, "data": None, "error": "missing_loki_query_url"}

    loki_query_url = _ensure_query_range_url(loki_query_url)
    ready_url = _build_ready_url(loki_query_url)

    logger.info("Validating connectivity to Loki: %s", loki_query_url)
    conn_ok = await _wait_for_connection(loki_query_url, retries=20, delay=2.0)
    if not conn_ok:
        logger.error("verify_event_ingestion_logs loki_unreachable")
        return {"success": False, "data": {"url": loki_query_url}, "error": "loki_unreachable"}

    logger.info("Checking Loki readiness at %s", ready_url)
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        try:
            req = urllib.request.Request(ready_url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.getcode() == 200:
                    logger.info("Loki ready")
                    break
        except Exception:
            pass
        await asyncio.sleep(1)
    else:
        return {"success": False, "data": None, "error": "loki_not_ready"}

    tried_urls = []
    attempt = 0
    q_start = time.time()

    while time.time() - q_start < timeout_seconds:
        attempt += 1

        try:
            query = urllib.parse.quote(logql, safe="")
            now = int(time.time() * 1e9)
            start_ns = now - (10 * 60 * 1e9)

            full = (
                f"{loki_query_url}?query={query}"
                f"&start={start_ns}&end={now}&direction=BACKWARD&limit=5000"
            )

            tried_urls.append(full)

            req = urllib.request.Request(full, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                code = resp.getcode()

                if code == 200:
                    parsed = json.loads(body)
                    results = parsed.get("data", {}).get("result", [])

                    if results:
                        logger.info("Ingestion success; matched %d results", len(results))
                        return {
                            "success": True,
                            "data": {
                                "results": len(results),
                                "attempts": attempt,
                                "url": full,
                                "response": body,
                            },
                            "error": None,
                        }

        except Exception as e:
            logger.debug("Query attempt %d failed: %s", attempt, e)

        await asyncio.sleep(poll_interval)

    return {
        "success": False,
        "data": {
            "tried": tried_urls[:5],
            "attempts": attempt,
            "elapsed": time.time() - q_start,
        },
        "error": "timeout_or_no_match",
    }