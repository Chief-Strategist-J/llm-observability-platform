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
            logger.debug("verify_can_connect_result url=%s host=%s port=%s success=%s", url, host, port, success)
            return success
    except Exception as e:
        logger.debug("verify_can_connect_exception url=%s error=%s", url, e)
        return False


async def _wait_for_connection(url: str, retries: int = 15, delay: float = 2.0) -> bool:
    logger.info("verify_wait_connection_start url=%s retries=%s delay=%s", url, retries, delay)
    for attempt in range(1, retries + 1):
        if _can_connect(url):
            logger.info("verify_wait_connection_success url=%s attempt=%s", url, attempt)
            return True
        logger.warning("verify_wait_connection_failed url=%s attempt=%s", url, attempt)
        await asyncio.sleep(delay)
    logger.error("verify_wait_connection_timeout url=%s retries=%s", url, retries)
    return False


def _build_ready_url(tempo_query_url: str) -> str:
    logger.debug("verify_build_ready_url_start url=%s", tempo_query_url)
    parsed = urllib.parse.urlparse(tempo_query_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    ready_url = f"{base}/ready"
    logger.debug("verify_build_ready_url_done base=%s ready_url=%s", base, ready_url)
    return ready_url


@activity.defn
async def verify_event_ingestion_tracings(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("verify_ingestion_start params_keys=%s", list(params.keys()))

    trace_id = params.get("trace_id")
    tempo_query_url = params.get("tempo_query_url")
    poll_interval = float(params.get("poll_interval", 2))
    timeout_seconds = int(params.get("timeout_seconds", 60))

    logger.info(
        "verify_params trace_id=%s tempo_url=%s poll_interval=%s timeout_seconds=%s",
        trace_id,
        tempo_query_url,
        poll_interval,
        timeout_seconds
    )

    if not trace_id:
        logger.error("verify_error error=missing_trace_id")
        return {"success": False, "data": None, "error": "missing_trace_id"}

    if not tempo_query_url:
        logger.error("verify_error error=missing_tempo_query_url")
        return {"success": False, "data": None, "error": "missing_tempo_query_url"}

    ready_url = _build_ready_url(tempo_query_url)
    logger.info("verify_urls tempo_query_url=%s ready_url=%s", tempo_query_url, ready_url)

    # Try initial connection with fewer retries
    conn_ok = await _wait_for_connection(tempo_query_url, retries=3, delay=2.0)
    
    if not conn_ok:
        logger.info("Initial URL %s unreachable, trying fallbacks", tempo_query_url)
        parsed = urllib.parse.urlparse(tempo_query_url)
        host_for_direct = "localhost"
        candidate_ports = [3200, 3201]
        if parsed.port:
            candidate_ports.insert(0, parsed.port)
            
        found_url = None
        for port in candidate_ports:
            # Construct fallback URL preserving path and query
            fallback_url = parsed._replace(netloc=f"{host_for_direct}:{port}").geturl()
            logger.debug("Checking fallback url: %s", fallback_url)
            if await _wait_for_connection(fallback_url, retries=2, delay=1.0):
                logger.info("Fallback URL reachable: %s", fallback_url)
                tempo_query_url = fallback_url
                found_url = fallback_url
                conn_ok = True
                break
                
        if not found_url:
            logger.error("verify_error error=tempo_unreachable url=%s", tempo_query_url)
            return {"success": False, "data": {"url": tempo_query_url}, "error": "tempo_unreachable"}
            
        # Update ready_url in case tempo_query_url changed
        ready_url = _build_ready_url(tempo_query_url)

    logger.info("verify_readiness_check_start ready_url=%s", ready_url)

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
                    logger.info(
                        "verify_ready_success attempt=%s elapsed=%.2f",
                        ready_checks,
                        time.time() - start_time
                    )
                    break
        except urllib.error.HTTPError as e:
            logger.debug("verify_ready_http_error attempt=%s code=%s", ready_checks, e.code)
        except Exception as e:
            logger.debug("verify_ready_exception attempt=%s error=%s", ready_checks, e)

        await asyncio.sleep(1)
    else:
        logger.error(
            "verify_readiness_timeout attempts=%s timeout_seconds=%s",
            ready_checks,
            timeout_seconds
        )
        return {"success": False, "data": {"ready_checks": ready_checks}, "error": "tempo_not_ready"}

    tried_urls = []
    attempt = 0
    query_start = time.time()

    logger.info("verify_trace_query_start trace_id=%s", trace_id)

    while time.time() - query_start < timeout_seconds:
        attempt += 1

        try:
            query_url = f"{tempo_query_url.rstrip('/')}/api/traces/{trace_id}"
            tried_urls.append(query_url)
            logger.debug("verify_query_attempt attempt=%s url=%s", attempt, query_url)

            req = urllib.request.Request(query_url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                code = resp.getcode()

                logger.debug(
                    "verify_query_response attempt=%s code=%s body_length=%s",
                    attempt,
                    code,
                    len(body)
                )

                if code == 200:
                    parsed = json.loads(body)

                    has_trace = False
                    if isinstance(parsed, dict):
                        batches = parsed.get("batches", [])
                        if batches:
                            has_trace = True
                        resource_spans = parsed.get("resourceSpans", [])
                        if resource_spans:
                            has_trace = True

                    logger.info("verify_query_trace_presence attempt=%s trace_found=%s", attempt, has_trace)

                    if has_trace:
                        elapsed = time.time() - query_start
                        logger.info("verify_ingestion_success attempts=%s elapsed=%.2f", attempt, elapsed)

                        return {
                            "success": True,
                            "data": {
                                "trace_found": True,
                                "attempts": attempt,
                                "url": query_url,
                                "response": body,
                            },
                            "error": None,
                        }
                    else:
                        logger.debug("verify_query_no_trace_data attempt=%s", attempt)

        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.debug("verify_query_not_found attempt=%s", attempt)
            else:
                logger.debug("verify_query_http_error attempt=%s code=%s", attempt, e.code)
        except Exception as e:
            logger.debug("verify_query_exception attempt=%s error=%s", attempt, e)

        await asyncio.sleep(poll_interval)

    elapsed = time.time() - query_start
    logger.error("verify_query_timeout attempts=%s elapsed=%.2f", attempt, elapsed)

    return {
        "success": False,
        "data": {
            "tried": tried_urls[:5],
            "attempts": attempt,
            "elapsed": elapsed,
        },
        "error": "timeout_or_no_match",
    }
