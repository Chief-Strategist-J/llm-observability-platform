import json
import logging
import urllib.request
import urllib.error
import urllib.parse
import base64
import socket
import asyncio
from typing import Any, Dict
from temporalio import activity

logger = logging.getLogger(__name__)


def _can_connect(url: str, timeout: float = 5.0) -> bool:
    logger.debug("datasource_metrics_can_connect_start url=%s timeout=%s", url, timeout)
    try:
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            success = result == 0
            logger.debug("datasource_metrics_can_connect_result url=%s result=%s", url, success)
            return success
    except Exception as e:
        logger.debug("datasource_metrics_can_connect_failed url=%s error=%s", url, e)
        return False


async def _wait_for_connection(url: str, retries: int = 15, delay: float = 2.0) -> bool:
    logger.info("datasource_metrics_wait_connection_start url=%s retries=%s", url, retries)
    for attempt in range(1, retries + 1):
        if _can_connect(url):
            logger.info("datasource_metrics_connection_success url=%s attempt=%s", url, attempt)
            return True
        logger.warning("datasource_metrics_connection_failed url=%s attempt=%s", url, attempt)
        await asyncio.sleep(delay)
    logger.error("datasource_metrics_connection_timeout url=%s", url)
    return False


@activity.defn
async def create_grafana_datasource_metrics(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("datasource_metrics_start params=%s", list(params.keys()))

    grafana_url = params.get("grafana_url")
    grafana_user = params.get("grafana_user")
    grafana_password = params.get("grafana_password")
    datasource_name = params.get("datasource_name")
    prometheus_url = params.get("prometheus_url")
    upsert_mode = params.get("upsert_mode", "upsert")

    logger.debug("datasource_metrics_params name=%s prom_url=%s grafana_url=%s", 
                datasource_name, prometheus_url, grafana_url)

    try:
        org_id = int(params.get("org_id", 1))
    except Exception:
        org_id = 1

    if not grafana_url or not datasource_name or not prometheus_url or not grafana_user or not grafana_password:
        logger.error("datasource_metrics_missing_fields")
        return {"success": False, "data": None, "error": "missing_required_fields"}

    logger.info("datasource_metrics_validating_grafana url=%s", grafana_url)

    resolved = await _wait_for_connection(grafana_url, retries=3, delay=2.0)
    
    if not resolved:
        logger.info("Original URL %s unreachable, trying localhost fallback", grafana_url)
        try:
            parsed = urllib.parse.urlparse(grafana_url)
            port = parsed.port or 3000
            fallback_url = parsed._replace(netloc=f"localhost:{port}").geturl()
            
            resolved = await _wait_for_connection(fallback_url, retries=10, delay=2.0)
            if resolved:
                logger.info("Localhost fallback successful: %s", fallback_url)
                grafana_url = fallback_url
        except Exception as e:
            logger.warning("Fallback attempt failed: %s", e)
            
    if not resolved:
        logger.error("datasource_metrics_grafana_unreachable url=%s", grafana_url)
        return {"success": False, "data": {"url": grafana_url}, "error": "grafana_unreachable"}

    try:
        auth_token = base64.b64encode(f"{grafana_user}:{grafana_password}".encode("utf-8")).decode("utf-8")
        headers = {"Authorization": f"Basic {auth_token}", "Content-Type": "application/json"}

        ds_def = {
            "name": datasource_name,
            "type": "prometheus",
            "access": "proxy",
            "url": prometheus_url.rstrip("/"),
            "isDefault": False,
            "jsonData": {},
            "orgId": org_id
        }

        logger.debug("datasource_metrics_definition ds=%s", ds_def)

        name_endpoint = grafana_url.rstrip("/") + f"/api/datasources/name/{urllib.parse.quote(datasource_name)}"
        get_req = urllib.request.Request(name_endpoint, headers=headers, method="GET")
        ds_id = None

        logger.debug("datasource_metrics_checking_existing url=%s", name_endpoint)

        try:
            with urllib.request.urlopen(get_req, timeout=10) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                existing = json.loads(body) if body else {}
                ds_id = existing.get("id")
                logger.info("datasource_metrics_existing_found id=%s", ds_id)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.info("datasource_metrics_not_found_will_create")
                ds_id = None
            else:
                err_body = getattr(e, "read", lambda: b"")().decode("utf-8", errors="ignore")
                logger.error("datasource_metrics_get_error code=%s body=%s", e.code, err_body)
                return {"success": False, "data": {"status": e.code, "body": err_body}, "error": "grafana_get_error"}
        except Exception as e:
            logger.exception("datasource_metrics_get_exception error=%s", e)
            return {"success": False, "data": None, "error": "grafana_unreachable"}

        if ds_id and upsert_mode == "upsert":
            update_endpoint = grafana_url.rstrip("/") + f"/api/datasources/{ds_id}"
            payload = json.dumps({**ds_def, "id": ds_id}).encode("utf-8")
            put_req = urllib.request.Request(update_endpoint, data=payload, headers=headers, method="PUT")

            logger.info("datasource_metrics_updating id=%s url=%s", ds_id, update_endpoint)

            try:
                with urllib.request.urlopen(put_req, timeout=10) as resp2:
                    body2 = resp2.read().decode("utf-8", errors="ignore")
                    logger.info("datasource_metrics_updated id=%s status=%s", ds_id, resp2.status)
                    return {"success": True, "data": {"status": resp2.status, "body": body2}, "error": None}
            except urllib.error.HTTPError as e2:
                err_body2 = getattr(e2, "read", lambda: b"")().decode("utf-8", errors="ignore")
                logger.error("datasource_metrics_update_error code=%s body=%s", e2.code, err_body2)
                return {"success": False, "data": {"status": e2.code, "body": err_body2}, "error": "grafana_update_error"}
            except Exception as e:
                logger.exception("datasource_metrics_update_exception error=%s", e)
                return {"success": False, "data": None, "error": "grafana_update_failed"}

        create_endpoint = grafana_url.rstrip("/") + "/api/datasources"
        payload = json.dumps(ds_def).encode("utf-8")
        post_req = urllib.request.Request(create_endpoint, data=payload, headers=headers, method="POST")

        logger.info("datasource_metrics_creating url=%s", create_endpoint)

        try:
            with urllib.request.urlopen(post_req, timeout=10) as resp3:
                body3 = resp3.read().decode("utf-8", errors="ignore")
                logger.info("datasource_metrics_created status=%s", resp3.status)
                return {"success": True, "data": {"status": resp3.status, "body": body3}, "error": None}
        except urllib.error.HTTPError as e3:
            err_body3 = getattr(e3, "read", lambda: b"")().decode("utf-8", errors="ignore")
            logger.error("datasource_metrics_create_error code=%s body=%s", e3.code, err_body3)
            return {"success": False, "data": {"status": e3.code, "body": err_body3}, "error": "grafana_create_error"}
        except Exception as e:
            logger.exception("datasource_metrics_create_exception error=%s", e)
            return {"success": False, "data": None, "error": "grafana_create_failed"}

    except Exception as e:
        logger.exception("datasource_metrics_fatal_error error=%s", e)
        return {"success": False, "data": None, "error": "unknown_error"}