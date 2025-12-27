from __future__ import annotations

import subprocess
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


@activity.defn(name="check_network_exists_activity")
async def check_network_exists_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        network_name: str = params["network_name"]
        logger.info("event=check_network_exists_start network=%s", network_name)
        result = run_command(["docker", "network", "ls", "--filter", f"name=^{network_name}$", "--format", "{{.Name}}"])
        exists = result["success"] and network_name in result["stdout"]
        logger.info("event=check_network_exists_complete network=%s exists=%s", network_name, exists)
        return {"success": True, "exists": exists, "network_name": network_name}
    except Exception as e:
        logger.error("event=check_network_exists_failed error=%s", str(e))
        return {"success": False, "error": str(e), "exists": False}


@activity.defn(name="delete_network_activity")
async def delete_network_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        network_name: str = params["network_name"]
        logger.info("event=delete_network_start network=%s", network_name)
        result = run_command(["docker", "network", "rm", network_name])
        logger.info("event=delete_network_complete network=%s success=%s", network_name, result["success"])
        return {"success": result["success"], "network_name": network_name, "stdout": result["stdout"]}
    except Exception as e:
        logger.error("event=delete_network_failed error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="create_network_activity")
async def create_network_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        network_name: str = params["network_name"]
        subnet: str = params.get("subnet", "172.29.0.0/16")
        gateway: str = params.get("gateway", "172.29.0.1")
        logger.info("event=create_network_start network=%s subnet=%s gateway=%s", network_name, subnet, gateway)
        result = run_command([
            "docker", "network", "create",
            "--driver", "bridge",
            "--subnet", subnet,
            "--gateway", gateway,
            network_name
        ])
        logger.info("event=create_network_complete network=%s success=%s", network_name, result["success"])
        return {"success": result["success"], "network_name": network_name, "subnet": subnet, "gateway": gateway}
    except Exception as e:
        logger.error("event=create_network_failed error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="inspect_network_activity")
async def inspect_network_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        network_name: str = params["network_name"]
        logger.info("event=inspect_network_start network=%s", network_name)
        result = run_command(["docker", "network", "inspect", network_name])
        if result["success"]:
            data = json.loads(result["stdout"])
            logger.info("event=inspect_network_complete network=%s containers=%d", network_name, len(data[0].get("Containers", {})) if data else 0)
            return {"success": True, "network_name": network_name, "data": data[0] if data else None}
        logger.error("event=inspect_network_failed network=%s stderr=%s", network_name, result["stderr"][:200])
        return {"success": False, "network_name": network_name, "error": result["stderr"]}
    except Exception as e:
        logger.error("event=inspect_network_exception error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="attach_container_to_network_activity")
async def attach_container_to_network_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        container_name: str = params["container_name"]
        network_name: str = params["network_name"]
        ip_address: str = params.get("ip_address", "")
        logger.info("event=attach_container_to_network_start container=%s network=%s ip=%s", container_name, network_name, ip_address)
        cmd = ["docker", "network", "connect"]
        if ip_address:
            cmd.extend(["--ip", ip_address])
        cmd.extend([network_name, container_name])
        result = run_command(cmd)
        logger.info("event=attach_container_to_network_complete container=%s network=%s success=%s", container_name, network_name, result["success"])
        return {"success": result["success"], "container_name": container_name, "network_name": network_name, "ip_address": ip_address}
    except Exception as e:
        logger.error("event=attach_container_to_network_failed error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="verify_network_attachment_activity")
async def verify_network_attachment_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        container_name: str = params["container_name"]
        network_name: str = params["network_name"]
        logger.info("event=verify_network_attachment_start container=%s network=%s", container_name, network_name)
        result = run_command(["docker", "inspect", container_name])
        if not result["success"]:
            logger.error("event=verify_network_attachment_failed container=%s error=%s", container_name, result["stderr"][:200])
            return {"success": False, "error": result["stderr"], "attached": False}
        data = json.loads(result["stdout"])
        if not data:
            return {"success": False, "error": "No inspect data", "attached": False}
        networks = data[0].get("NetworkSettings", {}).get("Networks", {})
        attached = network_name in networks
        logger.info("event=verify_network_attachment_complete container=%s network=%s attached=%s networks=%s", container_name, network_name, attached, list(networks.keys()))
        return {"success": True, "attached": attached, "container_name": container_name, "network_name": network_name, "networks": list(networks.keys())}
    except Exception as e:
        logger.error("event=verify_network_attachment_exception error=%s", str(e))
        return {"success": False, "error": str(e), "attached": False}
