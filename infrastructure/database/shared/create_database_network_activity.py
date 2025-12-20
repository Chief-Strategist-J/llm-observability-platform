from pathlib import Path
from typing import Dict, Any, List
from temporalio import activity
import time
import subprocess
import json
import logging

logger = logging.getLogger(__name__)


def run_command(cmd: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        return subprocess.CompletedProcess(cmd, 1, "", f"Command timed out: {e}")
    except Exception as e:
        return subprocess.CompletedProcess(cmd, 1, "", str(e))


def get_network_containers(network_name: str) -> List[Dict[str, str]]:
    try:
        inspect_result = run_command(["docker", "network", "inspect", network_name])
        if inspect_result.returncode != 0:
            return []
        
        data = json.loads(inspect_result.stdout or "[]")
        if not data:
            return []
        
        containers = []
        network_data = data[0]
        containers_dict = network_data.get("Containers", {})
        
        for container_id, container_info in containers_dict.items():
            containers.append({
                "id": container_id,
                "name": container_info.get("Name", ""),
                "ipv4": container_info.get("IPv4Address", ""),
            })
        
        return containers
    except Exception as e:
        logger.error(f"event=get_network_containers_failed network={network_name} error={str(e)}")
        return []


def disconnect_container_from_network(container_id: str, network_name: str, force: bool = True) -> bool:
    try:
        cmd = ["docker", "network", "disconnect"]
        if force:
            cmd.append("-f")
        cmd.extend([network_name, container_id])
        
        result = run_command(cmd)
        if result.returncode == 0:
            logger.info(f"event=container_disconnected container_id={container_id} network={network_name}")
            return True
        else:
            logger.warning(f"event=container_disconnect_failed container_id={container_id} network={network_name} stderr={result.stderr}")
            return False
    except Exception as e:
        logger.error(f"event=disconnect_container_exception container_id={container_id} network={network_name} error={str(e)}")
        return False


def remove_network_with_cleanup(network_name: str) -> bool:
    try:
        containers = get_network_containers(network_name)
        
        if containers:
            logger.info(f"event=network_has_active_endpoints network={network_name} container_count={len(containers)}")
            
            for container in containers:
                container_id = container["id"]
                container_name = container["name"]
                
                logger.info(f"event=disconnecting_container_from_network container_id={container_id} container_name={container_name} network={network_name}")
                
                if not disconnect_container_from_network(container_id, network_name, force=False):
                    logger.warning(f"event=retrying_disconnect_with_force container_id={container_id} network={network_name}")
                    disconnect_container_from_network(container_id, network_name, force=True)
            
            time.sleep(2)
        
        result = run_command(["docker", "network", "rm", network_name])
        if result.returncode == 0:
            logger.info(f"event=network_removed network={network_name}")
            return True
        else:
            logger.error(f"event=network_remove_failed network={network_name} stderr={result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"event=remove_network_with_cleanup_failed network={network_name} error={str(e)}")
        return False


@activity.defn(name="create_database_network_activity")
async def create_database_network_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    trace_id = params.get("trace_id", "db-network-create")
    network_name = params.get("network_name", "database-network")
    subnet = params.get("subnet", "172.29.0.0/16")
    gateway = params.get("gateway", "172.29.0.1")
    
    start_time = time.time()
    
    logger.info(f"event=create_database_network_start trace_id={trace_id} network={network_name} subnet={subnet} gateway={gateway}")
    
    try:
        inspect_result = run_command(["docker", "network", "inspect", network_name])

        if inspect_result.returncode == 0:
            existing_subnet = None
            existing_gateway = None
            try:
                inspect_data = json.loads(inspect_result.stdout or "[]")
                if inspect_data:
                    config_entries = inspect_data[0].get("IPAM", {}).get("Config", [])
                    if config_entries:
                        existing_subnet = config_entries[0].get("Subnet")
                        existing_gateway = config_entries[0].get("Gateway")
            except json.JSONDecodeError as exc:
                logger.warning(f"event=network_inspect_parse_failed network={network_name} error={str(exc)}")

            if existing_subnet == subnet and (not gateway or existing_gateway == gateway):
                logger.info(f"event=network_exists_with_correct_config network={network_name} subnet={existing_subnet}")
                duration_ms = int((time.time() - start_time) * 1000)
                return {
                    "success": True,
                    "service": "network-manager",
                    "network_name": network_name,
                    "created": False,
                    "exists": True,
                    "duration_ms": duration_ms,
                    "trace_id": trace_id
                }

            logger.warning(f"event=network_config_mismatch_recreating network={network_name} existing_subnet={existing_subnet} existing_gateway={existing_gateway} expected_subnet={subnet} expected_gateway={gateway}")

            if not remove_network_with_cleanup(network_name):
                duration_ms = int((time.time() - start_time) * 1000)
                return {
                    "success": False,
                    "service": "network-manager",
                    "network_name": network_name,
                    "error": "Failed to remove existing network with mismatched config",
                    "duration_ms": duration_ms,
                    "trace_id": trace_id,
                }
            
            time.sleep(3)

        create_cmd = [
            "docker", "network", "create",
            "--driver", "bridge",
            "--subnet", subnet,
            "--gateway", gateway,
            network_name
        ]
        create_result = run_command(create_cmd)
        
        if create_result.returncode == 0:
            logger.info(f"event=network_created network={network_name} subnet={subnet} gateway={gateway}")
            duration_ms = int((time.time() - start_time) * 1000)
            return {
                "success": True,
                "service": "network-manager",
                "network_name": network_name,
                "created": True,
                "duration_ms": duration_ms,
                "trace_id": trace_id
            }
        else:
            logger.error(f"event=network_creation_failed network={network_name} error={create_result.stderr}")
            duration_ms = int((time.time() - start_time) * 1000)
            return {
                "success": False,
                "service": "network-manager",
                "network_name": network_name,
                "error": create_result.stderr,
                "duration_ms": duration_ms,
                "trace_id": trace_id
            }
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(f"event=create_database_network_failed error={e}")
        return {
            "success": False,
            "service": "network-manager",
            "error": str(e),
            "duration_ms": duration_ms,
            "trace_id": trace_id
        }