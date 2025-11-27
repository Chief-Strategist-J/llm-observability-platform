import logging
from typing import Dict, Any
from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def get_argocd_app_status(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(
        "argocd_status_start",
        application_name=params.get("application_name")
    )

    application_name = params.get("application_name")

    if not application_name:
        logger.error(
            "argocd_status_error",
            error="missing_application_name"
        )
        return {
            "success": False,
            "data": None,
            "error": "missing_application_name"
        }

    try:
        import subprocess

        cmd = [
            "argocd", "app", "get",
            application_name,
            "--output", "json",
            "--grpc-web"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            logger.error(
                "argocd_status_failed",
                application_name=application_name,
                returncode=result.returncode,
                stderr=result.stderr[:500]
            )
            return {
                "success": False,
                "data": {"stderr": result.stderr},
                "error": "status_failed"
            }

        import json
        status_data = json.loads(result.stdout)

        health_status = status_data.get("status", {}).get("health", {}).get("status")
        sync_status = status_data.get("status", {}).get("sync", {}).get("status")

        logger.info(
            "argocd_status_success",
            application_name=application_name,
            health=health_status,
            sync=sync_status
        )

        return {
            "success": True,
            "data": {
                "application_name": application_name,
                "health_status": health_status,
                "sync_status": sync_status,
                "raw_status": status_data.get("status")
            },
            "error": None
        }

    except Exception as e:
        logger.exception(
            "argocd_status_error",
            application_name=application_name,
            error_type=type(e).__name__
        )
        return {
            "success": False,
            "data": None,
            "error": "status_error"
        }
