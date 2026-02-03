from __future__ import annotations

import subprocess
import logging
from typing import Dict, List, Any

from temporalio import activity

logger = logging.getLogger(__name__)


def run_command(command: List[str], timeout: int = 300) -> Dict[str, Any]:
    logger.info("event=command_execute command=%s", " ".join(command))
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        success = result.returncode == 0
        logger.info("event=command_result success=%s returncode=%d", success, result.returncode)
        if not success:
            logger.error("event=command_failed stderr=%s", result.stderr[:500])
        return {
            "success": success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        logger.error("event=command_timeout timeout=%d", timeout)
        return {"success": False, "stdout": "", "stderr": f"Timeout after {timeout}s", "returncode": -1}
    except Exception as e:
        logger.error("event=command_exception error=%s", str(e))
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


@activity.defn(name="check_image_exists_activity")
async def check_image_exists_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        image_name: str = params["image_name"]
        logger.info("event=check_image_exists_start image=%s", image_name)
        result = run_command(["docker", "images", "-q", image_name])
        exists = result["success"] and len(result["stdout"].strip()) > 0
        logger.info("event=check_image_exists_complete image=%s exists=%s", image_name, exists)
        return {"success": True, "exists": exists, "image_name": image_name}
    except Exception as e:
        logger.error("event=check_image_exists_failed error=%s", str(e))
        return {"success": False, "error": str(e), "exists": False}


@activity.defn(name="pull_image_activity")
async def pull_image_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        image_name: str = params["image_name"]
        logger.info("event=pull_image_start image=%s", image_name)
        result = run_command(["docker", "pull", image_name], timeout=600)
        logger.info("event=pull_image_complete image=%s success=%s", image_name, result["success"])
        return {
            "success": result["success"],
            "image_name": image_name,
            "stdout": result["stdout"][:1000],
            "stderr": result["stderr"][:1000]
        }
    except Exception as e:
        logger.error("event=pull_image_failed error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="remove_image_activity")
async def remove_image_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        image_name: str = params["image_name"]
        logger.info("event=remove_image_start image=%s", image_name)
        result = run_command(["docker", "rmi", image_name])
        logger.info("event=remove_image_complete image=%s success=%s", image_name, result["success"])
        return {"success": result["success"], "image_name": image_name}
    except Exception as e:
        logger.error("event=remove_image_failed error=%s", str(e))
        return {"success": False, "error": str(e)}
