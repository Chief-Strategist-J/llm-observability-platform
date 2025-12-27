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


@activity.defn(name="start_compose_activity")
async def start_compose_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        compose_path: str = params["compose_path"]
        project_name: str = params.get("project_name", "")
        logger.info("event=start_compose_start compose_path=%s project=%s", compose_path, project_name)
        cmd: List[str] = ["docker-compose", "-f", compose_path]
        if project_name:
            cmd.extend(["-p", project_name])
        cmd.extend(["up", "-d"])
        result = run_command(cmd, timeout=300)
        logger.info("event=start_compose_complete compose_path=%s success=%s", compose_path, result["success"])
        return {
            "success": result["success"],
            "compose_path": compose_path,
            "project_name": project_name,
            "stdout": result["stdout"][:1000]
        }
    except Exception as e:
        logger.error("event=start_compose_failed error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="stop_compose_activity")
async def stop_compose_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        compose_path: str = params["compose_path"]
        project_name: str = params.get("project_name", "")
        logger.info("event=stop_compose_start compose_path=%s project=%s", compose_path, project_name)
        cmd: List[str] = ["docker-compose", "-f", compose_path]
        if project_name:
            cmd.extend(["-p", project_name])
        cmd.append("down")
        result = run_command(cmd, timeout=120)
        logger.info("event=stop_compose_complete compose_path=%s success=%s", compose_path, result["success"])
        return {"success": result["success"], "compose_path": compose_path}
    except Exception as e:
        logger.error("event=stop_compose_failed error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="get_container_logs_activity")
async def get_container_logs_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        container_name: str = params["container_name"]
        lines: int = params.get("lines", 100)
        logger.info("event=get_container_logs_start container=%s lines=%d", container_name, lines)
        result = run_command(["docker", "logs", "--tail", str(lines), container_name])
        logger.info("event=get_container_logs_complete container=%s success=%s log_length=%d", container_name, result["success"], len(result["stdout"]))
        return {
            "success": result["success"],
            "container_name": container_name,
            "logs": result["stdout"][:5000],
            "stderr": result["stderr"][:2000]
        }
    except Exception as e:
        logger.error("event=get_container_logs_failed error=%s", str(e))
        return {"success": False, "error": str(e)}
