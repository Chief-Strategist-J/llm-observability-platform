import logging
import time
import asyncio
import socket
from typing import Dict, Any
from temporalio import activity
import urllib.request
import urllib.error
import urllib.parse
import json

logger = logging.getLogger(__name__)


def _can_connect(url: str, timeout: float = 5.0) -> bool:
    logger.debug("verify_can_connect_start url=%s timeout=%s", url, timeout)
    try:
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            success = result == 0
            logger.debug("verify_can_connect_result url=%s host=%s port=%s result=%s", url, host, port, success)
            return success
    except Exception as e:
        logger.debug("verify_can_connect_failed url=%s error=%s", url, e)
        return False


async def _wait_for_connection(url: str, retries: int = 15, delay: float = 2.0) -> bool:
    logger.info("verify_wait_connection_start url=%s retries=%s delay=%s", url, retries, delay)
    for attempt in range(1, retries + 1):
        if _can_connect(url):
            logger.info("verify_connection_success url=%s attempt=%s", url, attempt)
            return True
        logger.warning("verify_connection_failed url=%s attempt=%s", url, attempt)
        await asyncio.sleep(delay)
    logger.error("verify_connection_timeout url=%s retries=%s", url, retries)
    return False


def _ensure_query_range_url(loki_query_url: str) -> str:
    logger.debug("verify_ensure_query_range_start url=%s", loki_query_url)
    parsed = urllib.parse.urlparse(loki_query_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    if parsed.path.endswith("/query_range"):
        logger.debug("verify_ensure_query_range_already url=%s", loki_query_url)
        return loki_query_url
    if parsed.path.endswith("/query"):
        result = urllib.parse.urlunparse(
            (parsed.scheme, parsed.netloc,
             parsed.path[:-len("/query")] + "/query_range",
             "", parsed.query, "")
        )
        logger.debug("verify_ensure_query_range_converted from=%s to=%s", loki_query_url, result)
        return result
    result = f"{base}/loki/api/v1/query_range"
    logger.debug("verify_ensure_query_range_default from=%s to=%s", loki_query_url, result)
    return result


def _build_ready_url(loki_query_url: str) -> str:
    logger.debug("verify_build_ready_url_start url=%s", loki_query_url)
    parsed = urllib.parse.urlparse(loki_query_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    result = f"{base}/ready"
    logger.debug("verify_build_ready_url_result url=%s ready_url=%s", loki_query_url, result)
    return result


@activity.defn
async def verify_event_ingestion_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("verify_event_ingestion_start params=%s", list(params.keys()))

    logql = params.get("logql")
    loki_query_url = params.get("loki_query_url")
    poll_interval = float(params.get("poll_interval", 2))
    timeout_seconds = int(params.get("timeout_seconds", 60))

    logger.info("verify_params logql=%s url=%s poll=%s timeout=%s", logql, loki_query_url, poll_interval, timeout_seconds)

    if not logql:
        logger.error("verify_missing_logql")
        return {"success": False, "data": None, "error": "missing_logql"}

    if not loki_query_url:
        logger.error("verify_missing_loki_query_url")
        return {"success": False, "data": None, "error": "missing_loki_query_url"}

    loki_query_url = _ensure_query_range_url(loki_query_url)
    ready_url = _build_ready_url(loki_query_url)

    logger.info("verify_urls query_range=%s ready=%s", loki_query_url, ready_url)

    conn_ok = await _wait_for_connection(loki_query_url, retries=20, delay=2.0)
    if not conn_ok:
        logger.error("verify_loki_unreachable url=%s", loki_query_url)
        return {"success": False, "data": {"url": loki_query_url}, "error": "loki_unreachable"}

    logger.info("verify_checking_readiness url=%s", ready_url)
    start_time = time.time()
    ready_checks = 0

    while time.time() - start_time < timeout_seconds:
        ready_checks += 1
        try:
            req = urllib.request.Request(ready_url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                code = resp.getcode()
                logger.debug("verify_ready_check attempt=%s code=%s", ready_checks, code)
                if code == 200:
                    logger.info("verify_loki_ready attempt=%s elapsed=%.1f", ready_checks, time.time() - start_time)
                    break
        except urllib.error.HTTPError as e:
            logger.debug("verify_ready_check_http_error attempt=%s code=%s", ready_checks, e.code)
        except Exception as e:
            logger.debug("verify_ready_check_error attempt=%s error=%s", ready_checks, e)
        await asyncio.sleep(1)
    else:
        logger.error("verify_loki_not_ready checks=%s timeout=%s", ready_checks, timeout_seconds)
        return {"success": False, "data": {"ready_checks": ready_checks}, "error": "loki_not_ready"}

    tried_urls = []
    attempt = 0
    q_start = time.time()

    logger.info("verify_query_start logql=%s", logql)

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
            logger.debug("verify_query_attempt attempt=%s url=%s", attempt, full[:200])

            req = urllib.request.Request(full, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                code = resp.getcode()

                logger.debug("verify_query_response attempt=%s code=%s body_len=%s", attempt, code, len(body))

                if code == 200:
                    parsed = json.loads(body)
                    results = parsed.get("data", {}).get("result", [])

                    logger.info("verify_query_results attempt=%s results=%s", attempt, len(results))

                    if results:
                        logger.info("verify_ingestion_success results=%s attempts=%s elapsed=%.1f", 
                                  len(results), attempt, time.time() - q_start)
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
                    else:
                        logger.debug("verify_no_results attempt=%s", attempt)

        except urllib.error.HTTPError as e:
            logger.debug("verify_query_http_error attempt=%s code=%s", attempt, e.code)
        except Exception as e:
            logger.debug("verify_query_error attempt=%s error=%s", attempt, e)

        await asyncio.sleep(poll_interval)

    logger.error("verify_timeout attempts=%s elapsed=%.1f", attempt, time.time() - q_start)

    return {
        "success": False,
        "data": {
            "tried": tried_urls[:5],
            "attempts": attempt,
            "elapsed": time.time() - q_start,
        },
        "error": "timeout_or_no_match",
    }