from __future__ import annotations

import subprocess
import asyncio
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


@activity.defn(name="health_check_activity")
async def health_check_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        container_name: str = params["container_name"]
        health_check_command: List[str] = params["health_check_command"]
        max_retries: int = params.get("max_retries", 3)
        retry_delay: int = params.get("retry_delay", 5)
        logger.info("event=health_check_start container=%s command=%s max_retries=%d", container_name, " ".join(health_check_command), max_retries)
        for attempt in range(max_retries):
            cmd = ["docker", "exec", container_name] + health_check_command
            result = run_command(cmd, timeout=30)
            if result["success"]:
                logger.info("event=health_check_complete container=%s healthy=true attempts=%d", container_name, attempt + 1)
                return {
                    "success": True,
                    "healthy": True,
                    "container_name": container_name,
                    "attempts": attempt + 1,
                    "stdout": result["stdout"][:500]
                }
            if attempt < max_retries - 1:
                logger.info("event=health_check_retry container=%s attempt=%d", container_name, attempt + 1)
                await asyncio.sleep(retry_delay)
        logger.error("event=health_check_failed container=%s healthy=false attempts=%d", container_name, max_retries)
        return {"success": False, "healthy": False, "container_name": container_name, "attempts": max_retries, "stderr": result.get("stderr", "")[:500]}
    except Exception as e:
        logger.error("event=health_check_exception error=%s", str(e))
        return {"success": False, "error": str(e), "healthy": False}
