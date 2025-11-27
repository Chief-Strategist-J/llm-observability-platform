import logging
from typing import Dict, Any
from temporalio import activity

logger = logging.getLogger(__name__)


@activity.defn
async def deploy_to_argocd(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(
        "argocd_deploy_start",
        application_name=params.get("application_name"),
        namespace=params.get("namespace"),
        repo_url=params.get("repo_url")
    )
    
    application_name = params.get("application_name")
    namespace = params.get("namespace", "argocd")
    repo_url = params.get("repo_url")
    path = params.get("path")
    
    if not all([application_name, repo_url, path]):
        logger.error(
            "argocd_deploy_error",
            error="missing_required_params",
            has_app_name=bool(application_name),
            has_repo_url=bool(repo_url),
            has_path=bool(path)
        )
        return {
            "success": False,
            "data": None,
            "error": "missing_required_params"
        }
    
    try:
        import subprocess
        
        cmd = [
            "kubectl", "apply", "-f",
            f"infrastructure/cicd/argocd/applications/{application_name}.yaml",
            "-n", namespace
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            logger.error(
                "argocd_deploy_kubectl_failed",
                returncode=result.returncode,
                stderr=result.stderr[:500]
            )
            return {
                "success": False,
                "data": {"stderr": result.stderr},
                "error": "kubectl_apply_failed"
            }
        
        logger.info(
            "argocd_deploy_success",
            application_name=application_name,
            stdout_length=len(result.stdout)
        )
        
        return {
            "success": True,
            "data": {
                "application_name": application_name,
                "namespace": namespace,
                "stdout": result.stdout
            },
            "error": None
        }
        
    except subprocess.TimeoutExpired:
        logger.error(
            "argocd_deploy_timeout",
            application_name=application_name,
            timeout_seconds=60
        )
        return {
            "success": False,
            "data": None,
            "error": "deploy_timeout"
        }
    except Exception as e:
        logger.exception(
            "argocd_deploy_unexpected_error",
            application_name=application_name,
            error_type=type(e).__name__
        )
        return {
            "success": False,
            "data": None,
            "error": "unexpected_error"
        }


@activity.defn
async def sync_argocd_application(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(
        "argocd_sync_start",
        application_name=params.get("application_name")
    )
    
    application_name = params.get("application_name")
    
    if not application_name:
        logger.error(
            "argocd_sync_error",
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
            "argocd", "app", "sync",
            application_name,
            "--grpc-web"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode != 0:
            logger.error(
                "argocd_sync_failed",
                application_name=application_name,
                returncode=result.returncode,
                stderr=result.stderr[:500]
            )
            return {
                "success": False,
                "data": {"stderr": result.stderr},
                "error": "sync_failed"
            }
        
        logger.info(
            "argocd_sync_success",
            application_name=application_name
        )
        
        return {
            "success": True,
            "data": {
                "application_name": application_name,
                "stdout": result.stdout
            },
            "error": None
        }
        
    except Exception as e:
        logger.exception(
            "argocd_sync_error",
            application_name=application_name,
            error_type=type(e).__name__
        )
        return {
            "success": False,
            "data": None,
            "error": "sync_error"
        }
