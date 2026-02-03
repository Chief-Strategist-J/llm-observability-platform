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


def run_shell_command(command: str, timeout: int = 30) -> Dict[str, Any]:
    logger.info("event=shell_command_execute command=%s", command[:200])
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        success = result.returncode == 0
        logger.info("event=shell_command_result success=%s", success)
        return {"success": success, "stdout": result.stdout, "stderr": result.stderr}
    except Exception as e:
        logger.error("event=shell_command_exception error=%s", str(e))
        return {"success": False, "stdout": "", "stderr": str(e)}


@activity.defn(name="diagnostic_service_inspect_activity")
async def diagnostic_service_inspect_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        service_name: str = params["service_name"]
        logger.info("event=diagnostic_service_inspect_start service=%s", service_name)
        diagnostics: Dict[str, Any] = {}
        prev_spec = run_shell_command(f"docker service inspect {service_name} | jq -r '.[0].PreviousSpec // {{}}'")
        diagnostics["previous_spec"] = prev_spec["stdout"][:2000] if prev_spec["success"] else f"error: {prev_spec['stderr'][:200]}"
        timestamps = run_shell_command(f"docker service inspect {service_name} | jq -r '.[0] | {{CreatedAt:.CreatedAt, UpdatedAt:.UpdatedAt}}'")
        diagnostics["timestamps"] = timestamps["stdout"][:500] if timestamps["success"] else f"error: {timestamps['stderr'][:200]}"
        containers = run_shell_command(f"docker ps --filter 'label=com.docker.swarm.service.name={service_name}' --format '{{{{.ID}}}} {{{{.Image}}}} {{{{.Names}}}} {{{{.Status}}}}'")
        diagnostics["containers"] = containers["stdout"][:1000] if containers["success"] else f"error: {containers['stderr'][:200]}"
        resources = run_shell_command(f"docker service inspect {service_name} | jq -r '.[0].Spec.TaskTemplate.Resources // {{}}'")
        diagnostics["resources"] = resources["stdout"][:500] if resources["success"] else f"error: {resources['stderr'][:200]}"
        ports = run_shell_command(f"docker service inspect {service_name} | jq -r '.[0].Endpoint.Ports[]? | \"\\(.Protocol) \\(.PublishedPort)->\\(.TargetPort)\"'")
        diagnostics["ports"] = ports["stdout"][:500] if ports["success"] else f"error: {ports['stderr'][:200]}"
        labels = run_shell_command(f"docker service inspect {service_name} | jq -r '.[0].Spec.Labels // {{}}'")
        diagnostics["labels"] = labels["stdout"][:1000] if labels["success"] else f"error: {labels['stderr'][:200]}"
        logger.info("event=diagnostic_service_inspect_complete service=%s", service_name)
        return {"success": True, "service_name": service_name, "diagnostics": diagnostics}
    except Exception as e:
        logger.error("event=diagnostic_service_inspect_failed error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="diagnostic_container_inspect_activity")
async def diagnostic_container_inspect_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        container_name: str = params["container_name"]
        logger.info("event=diagnostic_container_inspect_start container=%s", container_name)
        diagnostics: Dict[str, Any] = {}
        healthcheck = run_shell_command(f"docker inspect {container_name} | jq -r '.[0].Config.Healthcheck // {{}}'")
        diagnostics["healthcheck"] = healthcheck["stdout"][:500] if healthcheck["success"] else f"error: {healthcheck['stderr'][:200]}"
        state = run_shell_command(f"docker inspect {container_name} | jq -r '.[0].State | {{OOMKilled:.OOMKilled, ExitCode:.ExitCode, StartedAt:.StartedAt, FinishedAt:.FinishedAt}}'")
        diagnostics["state"] = state["stdout"][:500] if state["success"] else f"error: {state['stderr'][:200]}"
        restart = run_shell_command(f"docker inspect {container_name} --format '{{{{.Id}}}} {{{{.State.Restarting}}}} {{{{.RestartCount}}}} {{{{.State.ExitCode}}}}'")
        diagnostics["restart_info"] = restart["stdout"][:200] if restart["success"] else f"error: {restart['stderr'][:200]}"
        mounts = run_shell_command(f"docker inspect {container_name} | jq -r '.[0].Mounts // []'")
        diagnostics["mounts"] = mounts["stdout"][:1000] if mounts["success"] else f"error: {mounts['stderr'][:200]}"
        networks = run_shell_command(f"docker inspect {container_name} | jq -r '.[0].NetworkSettings.Networks // {{}}'")
        diagnostics["networks"] = networks["stdout"][:1000] if networks["success"] else f"error: {networks['stderr'][:200]}"
        logger.info("event=diagnostic_container_inspect_complete container=%s", container_name)
        return {"success": True, "container_name": container_name, "diagnostics": diagnostics}
    except Exception as e:
        logger.error("event=diagnostic_container_inspect_failed error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="diagnostic_network_inspect_activity")
async def diagnostic_network_inspect_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        network_name: str = params["network_name"]
        logger.info("event=diagnostic_network_inspect_start network=%s", network_name)
        diagnostics: Dict[str, Any] = {}
        result = run_command(["docker", "network", "inspect", network_name])
        if result["success"]:
            data = json.loads(result["stdout"])
            if data:
                diagnostics["name"] = data[0].get("Name", "")
                diagnostics["driver"] = data[0].get("Driver", "")
                diagnostics["scope"] = data[0].get("Scope", "")
                diagnostics["ipam"] = data[0].get("IPAM", {})
                containers = data[0].get("Containers", {})
                diagnostics["container_count"] = len(containers)
                diagnostics["containers"] = {k[:12]: v.get("IPv4Address", "") for k, v in containers.items()}
        else:
            diagnostics["error"] = result["stderr"][:500]
        logger.info("event=diagnostic_network_inspect_complete network=%s containers=%d", network_name, diagnostics.get("container_count", 0))
        return {"success": True, "network_name": network_name, "diagnostics": diagnostics}
    except Exception as e:
        logger.error("event=diagnostic_network_inspect_failed error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="diagnostic_image_inspect_activity")
async def diagnostic_image_inspect_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        image_name: str = params["image_name"]
        logger.info("event=diagnostic_image_inspect_start image=%s", image_name)
        diagnostics: Dict[str, Any] = {}
        labels = run_shell_command(f"docker image inspect {image_name} | jq -r '.[0].Config.Labels // {{}} | to_entries[] | \"\\(.key)=\\(.value)\"'")
        diagnostics["labels"] = labels["stdout"][:1000] if labels["success"] else f"error: {labels['stderr'][:200]}"
        history = run_command(["docker", "history", "--format", "{{.CreatedBy}} {{.Size}}", image_name])
        diagnostics["history"] = history["stdout"][:2000] if history["success"] else f"error: {history['stderr'][:200]}"
        size = run_shell_command(f"docker image inspect {image_name} | jq -r '.[0].Size'")
        diagnostics["size_bytes"] = size["stdout"].strip() if size["success"] else "unknown"
        logger.info("event=diagnostic_image_inspect_complete image=%s", image_name)
        return {"success": True, "image_name": image_name, "diagnostics": diagnostics}
    except Exception as e:
        logger.error("event=diagnostic_image_inspect_failed error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="diagnostic_host_configuration_activity")
async def diagnostic_host_configuration_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        hostname: str = params.get("hostname", "")
        logger.info("event=diagnostic_host_configuration_start hostname=%s", hostname)
        diagnostics: Dict[str, Any] = {}
        hosts = run_shell_command("cat /etc/hosts | head -50")
        diagnostics["etc_hosts"] = hosts["stdout"][:2000] if hosts["success"] else f"error: {hosts['stderr'][:200]}"
        if hostname:
            grep = run_shell_command(f"grep -n '{hostname}' /etc/hosts || true")
            diagnostics["hostname_entries"] = grep["stdout"][:500] if grep["success"] else "not found"
            getent = run_shell_command(f"getent hosts {hostname} || true")
            diagnostics["getent_result"] = getent["stdout"][:200] if getent["success"] else "not resolved"
            ping = run_shell_command(f"ping -c 1 -W 2 {hostname} 2>&1 || true")
            diagnostics["ping_result"] = ping["stdout"][:300] if ping["success"] else ping["stderr"][:300]
        lo = run_shell_command("ip addr show lo | head -20")
        diagnostics["loopback"] = lo["stdout"][:500] if lo["success"] else f"error: {lo['stderr'][:200]}"
        nsswitch = run_shell_command("cat /etc/nsswitch.conf | grep hosts || true")
        diagnostics["nsswitch_hosts"] = nsswitch["stdout"][:200] if nsswitch["success"] else "not found"
        logger.info("event=diagnostic_host_configuration_complete hostname=%s", hostname)
        return {"success": True, "hostname": hostname, "diagnostics": diagnostics}
    except Exception as e:
        logger.error("event=diagnostic_host_configuration_failed error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="diagnostic_listening_ports_activity")
async def diagnostic_listening_ports_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        host_ip: str = params.get("host_ip", "127.0.2.1")
        hostname: str = params.get("hostname", "")
        logger.info("event=diagnostic_listening_ports_start host_ip=%s hostname=%s", host_ip, hostname)
        diagnostics: Dict[str, Any] = {}
        http_ports = run_shell_command("ss -ltnp | grep -E ':80|:443' || true")
        diagnostics["http_ports"] = http_ports["stdout"][:1000] if http_ports["success"] else f"error: {http_ports['stderr'][:200]}"
        ip_ports = run_shell_command(f"ss -ltnp | grep '{host_ip}' || true")
        diagnostics["host_ip_ports"] = ip_ports["stdout"][:500] if ip_ports["success"] else f"error: {ip_ports['stderr'][:200]}"
        if hostname:
            curl = run_shell_command(f"curl -Ik -H 'Host: {hostname}' https://{host_ip} --insecure -m 5 2>&1 || true")
            diagnostics["curl_result"] = curl["stdout"][:1000] if curl["success"] else curl["stderr"][:500]
        logger.info("event=diagnostic_listening_ports_complete host_ip=%s", host_ip)
        return {"success": True, "host_ip": host_ip, "diagnostics": diagnostics}
    except Exception as e:
        logger.error("event=diagnostic_listening_ports_failed error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="diagnostic_full_inspection_activity")
async def diagnostic_full_inspection_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        container_name: str = params.get("container_name", "")
        network_name: str = params.get("network_name", "")
        hostname: str = params.get("hostname", "")
        logger.info("event=diagnostic_full_inspection_start container=%s network=%s hostname=%s", container_name, network_name, hostname)
        full_diagnostics: Dict[str, Any] = {}
        if container_name:
            container_result = await diagnostic_container_inspect_activity({"container_name": container_name})
            full_diagnostics["container"] = container_result.get("diagnostics", {})
        if network_name:
            network_result = await diagnostic_network_inspect_activity({"network_name": network_name})
            full_diagnostics["network"] = network_result.get("diagnostics", {})
        if hostname:
            host_result = await diagnostic_host_configuration_activity({"hostname": hostname})
            full_diagnostics["host"] = host_result.get("diagnostics", {})
        ports_result = await diagnostic_listening_ports_activity({"hostname": hostname})
        full_diagnostics["ports"] = ports_result.get("diagnostics", {})
        logger.info("event=diagnostic_full_inspection_complete container=%s network=%s hostname=%s", container_name, network_name, hostname)
        return {"success": True, "diagnostics": full_diagnostics}
    except Exception as e:
        logger.error("event=diagnostic_full_inspection_failed error=%s", str(e))
        return {"success": False, "error": str(e)}
