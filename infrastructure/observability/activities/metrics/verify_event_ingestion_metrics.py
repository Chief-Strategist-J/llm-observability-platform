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
    logger.debug("verify_metrics_can_connect_start url=%s timeout=%s", url, timeout)
    try:
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            success = result == 0
            logger.debug("verify_metrics_can_connect_result url=%s host=%s port=%s result=%s", 
                        url, host, port, success)
            return success
    except Exception as e:
        logger.debug("verify_metrics_can_connect_failed url=%s error=%s", url, e)
        return False


async def _wait_for_connection(url: str, retries: int = 15, delay: float = 2.0) -> bool:
    logger.info("verify_metrics_wait_connection_start url=%s retries=%s delay=%s", url, retries, delay)
    for attempt in range(1, retries + 1):
        if _can_connect(url):
            logger.info("verify_metrics_connection_success url=%s attempt=%s", url, attempt)
            return True
        logger.warning("verify_metrics_connection_failed url=%s attempt=%s", url, attempt)
        await asyncio.sleep(delay)
    logger.error("verify_metrics_connection_timeout url=%s retries=%s", url, retries)
    return False


@activity.defn
async def verify_event_ingestion_metrics(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("verify_event_ingestion_metrics_start params=%s", list(params.keys()))

    promql = params.get("promql")
    prometheus_query_url = params.get("prometheus_query_url")
    poll_interval = float(params.get("poll_interval", 2))
    timeout_seconds = int(params.get("timeout_seconds", 60))

    logger.info("verify_metrics_params promql=%s url=%s poll=%s timeout=%s", 
                promql, prometheus_query_url, poll_interval, timeout_seconds)

    if not promql:
        logger.error("verify_metrics_missing_promql")
        return {"success": False, "data": None, "error": "missing_promql"}

    if not prometheus_query_url:
        logger.error("verify_metrics_missing_prometheus_query_url")
        return {"success": False, "data": None, "error": "missing_prometheus_query_url"}

    logger.info("verify_metrics_checking_connectivity url=%s", prometheus_query_url)
    conn_ok = await _wait_for_connection(prometheus_query_url, retries=20, delay=2.0)
    if not conn_ok:
        logger.error("verify_metrics_prometheus_unreachable url=%s", prometheus_query_url)
        return {"success": False, "data": {"url": prometheus_query_url}, "error": "prometheus_unreachable"}

    ready_url = prometheus_query_url.replace("/api/v1/query", "/-/ready")
    if "/-/ready" not in ready_url:
        parsed = urllib.parse.urlparse(prometheus_query_url)
        ready_url = f"{parsed.scheme}://{parsed.netloc}/-/ready"
    
    logger.info("verify_metrics_checking_readiness url=%s", ready_url)
    start_time = time.time()
    ready_checks = 0

    while time.time() - start_time < timeout_seconds:
        ready_checks += 1
        try:
            req = urllib.request.Request(ready_url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                code = resp.getcode()
                logger.debug("verify_metrics_ready_check attempt=%s code=%s", ready_checks, code)
                if code == 200:
                    logger.info("verify_metrics_prometheus_ready attempt=%s elapsed=%.1f", 
                              ready_checks, time.time() - start_time)
                    break
        except urllib.error.HTTPError as e:
            logger.debug("verify_metrics_ready_check_http_error attempt=%s code=%s", ready_checks, e.code)
        except Exception as e:
            logger.debug("verify_metrics_ready_check_error attempt=%s error=%s", ready_checks, e)
        await asyncio.sleep(1)
    else:
        logger.error("verify_metrics_prometheus_not_ready checks=%s timeout=%s", ready_checks, timeout_seconds)
        return {"success": False, "data": {"ready_checks": ready_checks}, "error": "prometheus_not_ready"}

    tried_urls = []
    attempt = 0
    q_start = time.time()

    logger.info("verify_metrics_query_start promql=%s", promql)

    while time.time() - q_start < timeout_seconds:
        attempt += 1

        try:
            query = urllib.parse.quote(promql, safe="")
            now = int(time.time())
            
            full = f"{prometheus_query_url}?query={query}&time={now}"

            tried_urls.append(full)
            logger.debug("verify_metrics_query_attempt attempt=%s url=%s", attempt, full[:200])

            req = urllib.request.Request(full, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                code = resp.getcode()

                logger.debug("verify_metrics_query_response attempt=%s code=%s body_len=%s", 
                           attempt, code, len(body))

                if code == 200:
                    parsed = json.loads(body)
                    results = parsed.get("data", {}).get("result", [])

                    logger.info("verify_metrics_query_results attempt=%s results=%s", attempt, len(results))

                    if results:
                        logger.info("verify_metrics_ingestion_success results=%s attempts=%s elapsed=%.1f", 
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
                        logger.debug("verify_metrics_no_results attempt=%s", attempt)

        except urllib.error.HTTPError as e:
            logger.debug("verify_metrics_query_http_error attempt=%s code=%s", attempt, e.code)
        except Exception as e:
            logger.debug("verify_metrics_query_error attempt=%s error=%s", attempt, e)

        await asyncio.sleep(poll_interval)

    logger.error("verify_metrics_timeout attempts=%s elapsed=%.1f", attempt, time.time() - q_start)

    return {
        "success": False,
        "data": {
            "tried": tried_urls[:5],
            "attempts": attempt,
            "elapsed": time.time() - q_start,
        },
        "error": "timeout_or_no_match",
    }