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
    logger.debug("Checking connectivity for URL: %s", url)
    try:
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        logger.debug("Parsed host=%s port=%s", host, port)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            logger.debug("Connectivity check result=%s for %s:%s", result, host, port)
            return result == 0
    except Exception as e:
        logger.debug("Connection check failed for %s with exception: %s", url, e)
        return False


async def _wait_for_connection(url: str, retries: int = 15, delay: float = 2.0) -> bool:
    logger.debug("Waiting for service connectivity to URL: %s (retries=%d delay=%f)", url, retries, delay)
    for attempt in range(1, retries + 1):
        logger.debug("Connectivity attempt %d/%d for %s", attempt, retries, url)
        if _can_connect(url):
            logger.info("Service reachable at %s on attempt=%d", url, attempt)
            return True
        logger.warning("Service not reachable at %s attempt=%d", url, attempt)
        await asyncio.sleep(delay)
    logger.debug("Service unreachable after %d attempts: %s", retries, url)
    return False


@activity.defn
async def create_grafana_datasource_tracings_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.debug("Entered create_grafana_datasource_tracings_activity with params: %s", params)
    logger.info("create_grafana_datasource_tracings_activity started with params keys: %s", list(params.keys()))

    grafana_url = params.get("grafana_url")
    grafana_user = params.get("grafana_user")
    grafana_password = params.get("grafana_password")
    datasource_name = params.get("datasource_name")
    tempo_url = params.get("tempo_url")
    upsert_mode = params.get("upsert_mode", "upsert")

    logger.debug("Resolved parameters grafana_url=%s datasource_name=%s tempo_url=%s upsert_mode=%s",
                 grafana_url, datasource_name, tempo_url, upsert_mode)

    try:
        org_id = int(params.get("org_id", 1))
        logger.debug("Resolved org_id=%d", org_id)
    except Exception as e:
        logger.debug("Failed to parse org_id, defaulting to 1: %s", e)
        org_id = 1

    if not grafana_url or not datasource_name or not tempo_url or not grafana_user or not grafana_password:
        logger.error("create_grafana_datasource_tracings_activity missing_required_fields")
        return {"success": False, "data": None, "error": "missing_required_fields"}

    logger.info("Validating connectivity to Grafana URL: %s", grafana_url)

    resolved = await _wait_for_connection(grafana_url, retries=20, delay=2.0)
    logger.debug("Connectivity check result for Grafana: %s", resolved)

    if not resolved:
        logger.error("create_grafana_datasource_tracings_activity cannot_connect_to_grafana")
        return {"success": False, "data": {"url": grafana_url}, "error": "grafana_unreachable"}

    try:
        auth_token = base64.b64encode(f"{grafana_user}:{grafana_password}".encode("utf-8")).decode("utf-8")
        headers = {"Authorization": f"Basic {auth_token}", "Content-Type": "application/json"}
        logger.debug("Prepared authorization header for Grafana requests")

        ds_def = {
            "name": datasource_name,
            "type": "tempo",
            "access": "proxy",
            "url": tempo_url.rstrip("/"),
            "isDefault": False,
            "jsonData": {},
            "orgId": org_id
        }
        logger.debug("Constructed datasource definition: %s", ds_def)

        name_endpoint = grafana_url.rstrip("/") + f"/api/datasources/name/{urllib.parse.quote(datasource_name)}"
        logger.debug("Datasource GET endpoint: %s", name_endpoint)

        get_req = urllib.request.Request(name_endpoint, headers=headers, method="GET")
        ds_id = None

        try:
            logger.debug("Attempting GET request for existing datasource")
            with urllib.request.urlopen(get_req, timeout=10) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                logger.debug("Received GET response body: %s", body)
                existing = json.loads(body) if body else {}
                ds_id = existing.get("id")
                logger.info("existing datasource id=%s", ds_id)
        except urllib.error.HTTPError as e:
            logger.debug("HTTPError on datasource GET: %s", e)
            if e.code == 404:
                logger.info("datasource not found; will create")
                ds_id = None
            else:
                err_body = getattr(e, "read", lambda: b"")().decode("utf-8", errors="ignore")
                logger.error("grafana_get_error %s %s", e.code, err_body)
                return {"success": False, "data": {"status": e.code, "body": err_body}, "error": "grafana_get_error"}
        except Exception as e:
            logger.exception("Grafana unreachable GET: %s", e)
            return {"success": False, "data": None, "error": "grafana_unreachable"}

        if ds_id and upsert_mode == "upsert":
            logger.debug("Updating existing datasource id=%s", ds_id)

            update_endpoint = grafana_url.rstrip("/") + f"/api/datasources/{ds_id}"
            payload = json.dumps({**ds_def, "id": ds_id}).encode("utf-8")
            logger.debug("Update request payload: %s", payload)

            put_req = urllib.request.Request(update_endpoint, data=payload, headers=headers, method="PUT")

            try:
                with urllib.request.urlopen(put_req, timeout=10) as resp2:
                    body2 = resp2.read().decode("utf-8", errors="ignore")
                    logger.debug("Update response body: %s", body2)
                    logger.info("Datasource updated successfully")
                    return {"success": True, "data": {"status": resp2.status, "body": body2}, "error": None}
            except urllib.error.HTTPError as e2:
                err_body2 = getattr(e2, "read", lambda: b"")().decode("utf-8", errors="ignore")
                logger.error("grafana_update_error %s %s", e2.code, err_body2)
                return {"success": False, "data": {"status": e2.code, "body": err_body2}, "error": "grafana_update_error"}
            except Exception as e:
                logger.exception("grafana_update_failed: %s", e)
                return {"success": False, "data": None, "error": "grafana_update_failed"}

        create_endpoint = grafana_url.rstrip("/") + "/api/datasources"
        payload = json.dumps(ds_def).encode("utf-8")
        logger.debug("Create datasource payload: %s", payload)
        post_req = urllib.request.Request(create_endpoint, data=payload, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(post_req, timeout=10) as resp3:
                body3 = resp3.read().decode("utf-8", errors="ignore")
                logger.debug("Create response body: %s", body3)
                logger.info("Datasource created successfully")
                return {"success": True, "data": {"status": resp3.status, "body": body3}, "error": None}
        except urllib.error.HTTPError as e3:
            err_body3 = getattr(e3, "read", lambda: b"")().decode("utf-8", errors="ignore")
            logger.error("grafana_create_error %s %s", e3.code, err_body3)
            return {"success": False, "data": {"status": e3.code, "body": err_body3}, "error": "grafana_create_error"}
        except Exception as e:
            logger.exception("grafana_create_failed: %s", e)
            return {"success": False, "data": None, "error": "grafana_create_failed"}

    except Exception as e:
        logger.exception("fatal_error: %s", e)
        return {"success": False, "data": None, "error": "unknown_error"}
