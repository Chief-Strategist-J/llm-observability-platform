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
    logger.debug("verify_logs_can_connect url=%s timeout=%s", url, timeout)
    try:
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            success = result == 0
            logger.debug("verify_logs_can_connect result=%s", success)
            return success
    except Exception as e:
        logger.debug("verify_logs_can_connect_failed error=%s", e)
        return False


async def _wait_for_connection(url: str, retries: int = 15, delay: float = 2.0) -> bool:
    logger.info("verify_logs_wait_connection url=%s retries=%s delay=%s", url, retries, delay)
    for attempt in range(1, retries + 1):
        if _can_connect(url):
            logger.info("verify_logs_connection_success attempt=%s", attempt)
            return True
        logger.warning("verify_logs_connection_failed attempt=%s", attempt)
        await asyncio.sleep(delay)
    logger.error("verify_logs_connection_timeout retries=%s", retries)
    return False


def _ensure_query_range_url(loki_query_url: str) -> str:
    logger.debug("verify_logs_ensure_query_range url=%s", loki_query_url)
    parsed = urllib.parse.urlparse(loki_query_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    if parsed.path.endswith("/query_range"):
        logger.debug("verify_logs_already_query_range")
        return loki_query_url
    if parsed.path.endswith("/query"):
        result = urllib.parse.urlunparse(
            (parsed.scheme, parsed.netloc,
             parsed.path[:-len("/query")] + "/query_range",
             "", parsed.query, "")
        )
        logger.debug("verify_logs_converted_to_query_range result=%s", result)
        return result
    result = f"{base}/loki/api/v1/query_range"
    logger.debug("verify_logs_default_query_range result=%s", result)
    return result


def _build_ready_url(loki_query_url: str) -> str:
    logger.debug("verify_logs_build_ready url=%s", loki_query_url)
    parsed = urllib.parse.urlparse(loki_query_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    result = f"{base}/ready"
    logger.debug("verify_logs_ready_url result=%s", result)
    return result

@activity.defn
async def verify_event_ingestion_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("verify_logs_ingestion_start params_keys=%s", list(params.keys()))

    logql = params.get("logql")
    loki_query_url = params.get("loki_query_url")
    poll_interval = float(params.get("poll_interval", 2))
    timeout_seconds = int(params.get("timeout_seconds", 60))

    logger.info("verify_logs_params logql=%s url=%s poll=%s timeout=%s", 
                logql, loki_query_url, poll_interval, timeout_seconds)

    if not logql:
        logger.error("verify_logs_missing_logql")
        return {"success": False, "data": None, "error": "missing_logql"}

    if not loki_query_url:
        logger.error("verify_logs_missing_loki_query_url")
        return {"success": False, "data": None, "error": "missing_loki_query_url"}

    loki_query_url = _ensure_query_range_url(loki_query_url)
    ready_url = _build_ready_url(loki_query_url)

    logger.info("verify_logs_urls query_range=%s ready=%s", loki_query_url, ready_url)

    # Try initial connection with fewer retries
    conn_ok = await _wait_for_connection(loki_query_url, retries=3, delay=2.0)
    
    if not conn_ok:
        logger.info("Initial URL %s unreachable, trying fallbacks", loki_query_url)
        parsed = urllib.parse.urlparse(loki_query_url)
        host_for_direct = "localhost"
        candidate_ports = [3100, 31002]
        if parsed.port:
            candidate_ports.insert(0, parsed.port)
            
        found_url = None
        for port in candidate_ports:
            # Construct fallback URL preserving path and query
            fallback_url = parsed._replace(netloc=f"{host_for_direct}:{port}").geturl()
            logger.debug("Checking fallback url: %s", fallback_url)
            if await _wait_for_connection(fallback_url, retries=2, delay=1.0):
                logger.info("Fallback URL reachable: %s", fallback_url)
                loki_query_url = fallback_url
                found_url = fallback_url
                conn_ok = True
                break
                
        if not found_url:
            logger.error("verify_logs_unreachable url=%s", loki_query_url)
            return {"success": False, "data": {"url": loki_query_url}, "error": "loki_unreachable"}
            
        # Update ready_url in case loki_query_url changed
        ready_url = _build_ready_url(loki_query_url)

    logger.info("verify_logs_checking_readiness url=%s", ready_url)
    start_time = time.time()
    ready_checks = 0

    parsed = urllib.parse.urlparse(loki_query_url)
    host_for_direct = "localhost"
    candidate_ports = []
    try:
        if parsed.port:
            candidate_ports.append(parsed.port)
    except Exception:
        pass
    candidate_ports.extend([3100, 31002])
    candidate_ports = [p for p in candidate_ports if p]

    while time.time() - start_time < timeout_seconds:
        ready_checks += 1
        try:
            req = urllib.request.Request(ready_url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                code = resp.getcode()
                logger.debug("verify_logs_ready_check attempt=%s code=%s", ready_checks, code)
                if code == 200:
                    logger.info("verify_logs_ready attempt=%s elapsed=%.1f", 
                              ready_checks, time.time() - start_time)
                    break
        except urllib.error.HTTPError as e:
            logger.debug("verify_logs_ready_http_error attempt=%s code=%s", ready_checks, e.code)
        except Exception as e:
            logger.debug("verify_logs_ready_error attempt=%s error=%s", ready_checks, e)

        for port in candidate_ports:
            try:
                alt_ready = f"http://{host_for_direct}:{port}/ready"
                req = urllib.request.Request(alt_ready, method="GET")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    code = resp.getcode()
                    logger.debug("verify_logs_alt_ready port=%s attempt=%s code=%s", 
                               port, ready_checks, code)
                    if code == 200:
                        logger.info("verify_logs_ready_alt port=%s attempt=%s elapsed=%.1f", 
                                  port, ready_checks, time.time() - start_time)
                        ready_url = alt_ready
                        loki_query_url = f"http://{host_for_direct}:{port}/loki/api/v1/query_range"
                        break
            except urllib.error.HTTPError as e:
                logger.debug("verify_logs_alt_ready_http_error port=%s attempt=%s code=%s", 
                           port, ready_checks, getattr(e, "code", None))
            except Exception as e:
                logger.debug("verify_logs_alt_ready_error port=%s attempt=%s error=%s", 
                           port, ready_checks, e)
        else:
            await asyncio.sleep(1)
            continue
        break
    else:
        logger.error("verify_logs_not_ready checks=%s timeout=%s", ready_checks, timeout_seconds)
        return {"success": False, "data": {"ready_checks": ready_checks}, "error": "loki_not_ready"}

    tried_urls = []
    attempt = 0
    q_start = time.time()

    logger.info("verify_logs_query_start logql=%s", logql)

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
            logger.debug("verify_logs_query_attempt attempt=%s", attempt)

            req = urllib.request.Request(full, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                code = resp.getcode()

                logger.debug("verify_logs_query_response attempt=%s code=%s body_len=%s", 
                           attempt, code, len(body))

                if code == 200:
                    parsed_body = json.loads(body)
                    results = parsed_body.get("data", {}).get("result", [])

                    logger.info("verify_logs_query_results attempt=%s results=%s", attempt, len(results))

                    if results:
                        logger.info("verify_logs_ingestion_success results=%s attempts=%s elapsed=%.1f",
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
                        logger.debug("verify_logs_no_results attempt=%s", attempt)

        except urllib.error.HTTPError as e:
            logger.debug("verify_logs_query_http_error attempt=%s code=%s", attempt, e.code)
        except Exception as e:
            logger.debug("verify_logs_query_error attempt=%s error=%s", attempt, e)

        await asyncio.sleep(poll_interval)

    logger.error("verify_logs_timeout attempts=%s elapsed=%.1f", attempt, time.time() - q_start)

    return {
        "success": False,
        "data": {
            "tried": tried_urls[:5],
            "attempts": attempt,
            "elapsed": time.time() - q_start,
        },
        "error": "timeout_or_no_match",
    }