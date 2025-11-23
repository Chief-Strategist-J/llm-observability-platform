# infrastructure/observability/activities/log/create_grafana_datasource_activity.py

import json
import logging
import urllib.request
import urllib.error
import urllib.parse
import base64
from typing import Any, Dict
from temporalio import activity

logger = logging.getLogger(__name__)

@activity.defn
async def create_grafana_datasource_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("create_grafana_datasource_activity started with params keys: %s", list(params.keys()))

    grafana_url = params.get("grafana_url")
    grafana_user = params.get("grafana_user")
    grafana_password = params.get("grafana_password")
    datasource_name = params.get("datasource_name")
    loki_url = params.get("loki_url")
    upsert_mode = params.get("upsert_mode", "upsert")
    try:
        org_id = int(params.get("org_id", 1))
    except Exception:
        org_id = 1

    if not grafana_url or not datasource_name or not loki_url or not grafana_user or not grafana_password:
        logger.error("create_grafana_datasource_activity missing_required_fields")
        return {"success": False, "data": None, "error": "missing_required_fields"}

    try:
        auth_token = base64.b64encode(f"{grafana_user}:{grafana_password}".encode("utf-8")).decode("utf-8")
        headers = {"Authorization": f"Basic {auth_token}", "Content-Type": "application/json"}

        ds_def = {
            "name": datasource_name,
            "type": "loki",
            "access": "proxy",
            "url": loki_url.rstrip("/"),
            "isDefault": False,
            "jsonData": {},
            "orgId": org_id
        }

        name_endpoint = grafana_url.rstrip("/") + f"/api/datasources/name/{urllib.parse.quote(datasource_name)}"
        get_req = urllib.request.Request(name_endpoint, headers=headers, method="GET")
        ds_id = None
        try:
            with urllib.request.urlopen(get_req, timeout=10) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                existing = json.loads(body) if body else {}
                ds_id = existing.get("id")
                logger.info("create_grafana_datasource_activity found existing datasource id=%s", ds_id)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.info("create_grafana_datasource_activity datasource not found (will create)")
                ds_id = None
            else:
                try:
                    err_body = e.read().decode("utf-8", errors="ignore")
                except Exception:
                    err_body = ""
                logger.error("create_grafana_datasource_activity grafana_get_error code=%s body=%s", getattr(e, "code", None), err_body)
                return {"success": False, "data": {"status": getattr(e, "code", None), "body": err_body}, "error": "grafana_get_error"}
        except Exception as e:
            logger.exception("create_grafana_datasource_activity error contacting Grafana GET: %s", e)
            return {"success": False, "data": None, "error": "grafana_unreachable"}

        if ds_id and upsert_mode == "upsert":
            update_endpoint = grafana_url.rstrip("/") + f"/api/datasources/{ds_id}"
            payload = json.dumps({**ds_def, "id": ds_id}).encode("utf-8")
            put_req = urllib.request.Request(update_endpoint, data=payload, headers=headers, method="PUT")
            try:
                with urllib.request.urlopen(put_req, timeout=10) as resp2:
                    body2 = resp2.read().decode("utf-8", errors="ignore")
                    logger.info("create_grafana_datasource_activity grafana_datasource_updated id=%s", ds_id)
                    return {"success": True, "data": {"status": resp2.status, "body": body2, "id": ds_id}, "error": None}
            except urllib.error.HTTPError as e2:
                try:
                    err_body2 = e2.read().decode("utf-8", errors="ignore")
                except Exception:
                    err_body2 = ""
                logger.error("create_grafana_datasource_activity grafana_update_error %s %s", getattr(e2, "code", None), err_body2)
                return {"success": False, "data": {"status": getattr(e2, "code", None), "body": err_body2}, "error": "grafana_update_error"}
            except Exception as e:
                logger.exception("create_grafana_datasource_activity unexpected update error: %s", e)
                return {"success": False, "data": None, "error": "grafana_update_failed"}

        create_endpoint = grafana_url.rstrip("/") + "/api/datasources"
        payload = json.dumps(ds_def).encode("utf-8")
        post_req = urllib.request.Request(create_endpoint, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(post_req, timeout=10) as resp3:
                body3 = resp3.read().decode("utf-8", errors="ignore")
                logger.info("create_grafana_datasource_activity grafana_datasource_created")
                return {"success": True, "data": {"status": resp3.status, "body": body3}, "error": None}
        except urllib.error.HTTPError as e3:
            try:
                err_body3 = e3.read().decode("utf-8", errors="ignore")
            except Exception:
                err_body3 = ""
            logger.error("create_grafana_datasource_activity grafana_create_error %s %s", getattr(e3, "code", None), err_body3)
            return {"success": False, "data": {"status": getattr(e3, "code", None), "body": err_body3}, "error": "grafana_create_error"}
        except Exception as e:
            logger.exception("create_grafana_datasource_activity unexpected POST error: %s", e)
            return {"success": False, "data": None, "error": "grafana_create_failed"}

    except Exception as e:
        logger.exception("create_grafana_datasource_activity general error: %s", e)
        return {"success": False, "data": None, "error": "unknown_error"}
