from __future__ import annotations

import subprocess
import asyncio
import json
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


@activity.defn(name="check_container_exists_activity")
async def check_container_exists_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        container_name: str = params["container_name"]
        logger.info("event=check_container_exists_start container=%s", container_name)
        result = run_command(["docker", "ps", "-a", "-q", "-f", f"name=^{container_name}$"])
        exists = result["success"] and len(result["stdout"].strip()) > 0
        logger.info("event=check_container_exists_complete container=%s exists=%s", container_name, exists)
        return {"success": True, "exists": exists, "container_name": container_name}
    except Exception as e:
        logger.error("event=check_container_exists_failed error=%s", str(e))
        return {"success": False, "error": str(e), "exists": False}


@activity.defn(name="stop_container_activity")
async def stop_container_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        container_name: str = params["container_name"]
        logger.info("event=stop_container_start container=%s", container_name)
        result = run_command(["docker", "stop", container_name], timeout=60)
        logger.info("event=stop_container_complete container=%s success=%s", container_name, result["success"])
        return {"success": result["success"], "container_name": container_name, "stdout": result["stdout"]}
    except Exception as e:
        logger.error("event=stop_container_failed error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="remove_container_activity")
async def remove_container_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        container_name: str = params["container_name"]
        logger.info("event=remove_container_start container=%s", container_name)
        result = run_command(["docker", "rm", "-f", container_name])
        logger.info("event=remove_container_complete container=%s success=%s", container_name, result["success"])
        return {"success": result["success"], "container_name": container_name, "stdout": result["stdout"]}
    except Exception as e:
        logger.error("event=remove_container_failed error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="restart_container_activity")
async def restart_container_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        container_name: str = params["container_name"]
        logger.info("event=restart_container_start container=%s", container_name)
        result = run_command(["docker", "restart", container_name], timeout=60)
        await asyncio.sleep(5)
        logger.info("event=restart_container_complete container=%s success=%s", container_name, result["success"])
        return {"success": result["success"], "container_name": container_name, "stdout": result["stdout"]}
    except Exception as e:
        logger.error("event=restart_container_failed error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="verify_container_running_activity")
async def verify_container_running_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        container_name: str = params["container_name"]
        max_retries: int = params.get("max_retries", 5)
        retry_delay: int = params.get("retry_delay", 3)
        logger.info("event=verify_container_running_start container=%s max_retries=%d", container_name, max_retries)
        for attempt in range(max_retries):
            result = run_command([
                "docker", "ps", "--filter", f"name=^{container_name}$",
                "--filter", "status=running", "--format", "{{.Names}}"
            ])
            is_running = result["success"] and container_name in result["stdout"]
            if is_running:
                logger.info("event=verify_container_running_complete container=%s running=true attempts=%d", container_name, attempt + 1)
                return {"success": True, "running": True, "container_name": container_name, "attempts": attempt + 1}
            if attempt < max_retries - 1:
                logger.info("event=verify_container_running_retry container=%s attempt=%d", container_name, attempt + 1)
                await asyncio.sleep(retry_delay)
        logger.error("event=verify_container_running_failed container=%s attempts=%d", container_name, max_retries)
        return {"success": False, "running": False, "container_name": container_name, "attempts": max_retries}
    except Exception as e:
        logger.error("event=verify_container_running_exception error=%s", str(e))
        return {"success": False, "error": str(e), "running": False}


@activity.defn(name="inspect_container_activity")
async def inspect_container_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        container_name: str = params["container_name"]
        logger.info("event=inspect_container_start container=%s", container_name)
        result = run_command(["docker", "inspect", container_name])
        if result["success"]:
            data = json.loads(result["stdout"])
            container_data = data[0] if data else None
            if container_data:
                filtered_data = {
                    "Id": container_data.get("Id", "")[:12],
                    "State": container_data.get("State", {}),
                    "NetworkSettings": {"Networks": container_data.get("NetworkSettings", {}).get("Networks", {})}
                }
                logger.info("event=inspect_container_complete container=%s state=%s", container_name, filtered_data.get("State", {}).get("Status"))
                return {"success": True, "container_name": container_name, "data": filtered_data}
        logger.error("event=inspect_container_failed container=%s stderr=%s", container_name, result["stderr"][:200])
        return {"success": False, "container_name": container_name, "error": result["stderr"]}
    except Exception as e:
        logger.error("event=inspect_container_exception error=%s", str(e))
        return {"success": False, "error": str(e)}
