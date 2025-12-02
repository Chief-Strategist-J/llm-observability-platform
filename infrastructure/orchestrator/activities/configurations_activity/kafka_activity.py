from pathlib import Path
from typing import Dict
import logging
from temporalio import activity
from infrastructure.orchestrator.base import YAMLContainerManager
from infrastructure.orchestrator.base.port_manager import PortManager


logger = logging.getLogger(__name__)

KAFKA_YAML = Path(__file__).parent.parent.parent / "config" / "docker" / "kafka-dynamic-docker.yaml"


def _find_available_port(pm: PortManager, start_port: int, attempts: int = 50) -> int:
    if pm.check_port_available(start_port):
        return start_port

    for offset in range(1, attempts + 1):
        candidate = start_port + offset
        if pm.check_port_available(candidate):
            logger.warning(
                "event=kafka_port_relocated reason=port_in_use previous_port=%s new_port=%s",
                start_port,
                candidate,
            )
            return candidate

    raise RuntimeError(
        f"Unable to allocate a free port near {start_port}. "
        "Please free the port or specify 'broker_port' in workflow params."
    )


def _build_env(instance_id: int, params: dict) -> Dict[str, str]:
    env_overrides = {k: str(v) for k, v in (params.get("env_vars") or {}).items()}
    env_overrides.setdefault("KAFKA_INSTANCE_ID", str(instance_id))

    pm = PortManager()

    requested_broker = params.get("broker_port") or params.get("KAFKA_BROKER_PORT")
    base_broker = int(requested_broker) if requested_broker else pm.get_port("kafka", instance_id, "broker_port")
    broker_port = _find_available_port(pm, base_broker)
    env_overrides["KAFKA_BROKER_PORT"] = str(broker_port)

    requested_controller = params.get("controller_port") or params.get("KAFKA_CONTROLLER_PORT")
    base_controller = (
        int(requested_controller) if requested_controller else pm.get_port("kafka", instance_id, "controller_port")
    )
    controller_port = base_controller if pm.check_port_available(base_controller) else _find_available_port(
        pm, base_controller
    )
    env_overrides["KAFKA_CONTROLLER_PORT"] = str(controller_port)

    # Ensure advertised listeners matches broker port (important if we had to relocate)
    env_overrides.setdefault("KAFKA_ADVERTISED_LISTENERS", f"PLAINTEXT://localhost:{broker_port}")

    optional_mappings = {
        "cluster_id": "KAFKA_CLUSTER_ID",
        "memory_limit": "KAFKA_MEMORY_LIMIT",
        "memory_reservation": "KAFKA_MEMORY_RESERVATION",
        "cpu_limit": "KAFKA_CPU_LIMIT",
        "messaging_network": "MESSAGING_NETWORK",
        "health_interval": "HEALTH_CHECK_INTERVAL",
        "health_timeout": "HEALTH_CHECK_TIMEOUT",
    }

    for param_key, env_key in optional_mappings.items():
        if param_key in params and params[param_key] is not None:
            env_overrides[env_key] = str(params[param_key])

    return env_overrides


@activity.defn(name="start_kafka_activity")
async def start_kafka_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(
        str(KAFKA_YAML),
        instance_id=instance_id,
        env_vars=_build_env(instance_id, params),
    )
    
    success = manager.start(restart_if_running=True)
    
    return {
        "success": success,
        "service": "kafka",
        "instance_id": instance_id,
        "status": manager.get_status().value
    }


@activity.defn(name="stop_kafka_activity")
async def stop_kafka_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    force = params.get("force", True)
    manager = YAMLContainerManager(
        str(KAFKA_YAML),
        instance_id=instance_id,
        env_vars=_build_env(instance_id, params),
    )
    
    success = manager.stop(force=force)
    
    return {
        "success": success,
        "service": "kafka",
        "instance_id": instance_id,
        "force": force
    }


@activity.defn(name="restart_kafka_activity")
async def restart_kafka_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(
        str(KAFKA_YAML),
        instance_id=instance_id,
        env_vars=_build_env(instance_id, params),
    )
    
    success = manager.restart()
    
    return {
        "success": success,
        "service": "kafka",
        "instance_id": instance_id,
        "status": manager.get_status().value
    }


@activity.defn(name="delete_kafka_activity")
async def delete_kafka_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    remove_volumes = params.get("remove_volumes", True)
    remove_images = params.get("remove_images", True)
    remove_networks = params.get("remove_networks", False)
    
    manager = YAMLContainerManager(
        str(KAFKA_YAML),
        instance_id=instance_id,
        env_vars=_build_env(instance_id, params),
    )
    
    success = manager.delete(
        remove_volumes=remove_volumes,
        remove_images=remove_images,
        remove_networks=remove_networks
    )
    
    return {
        "success": success,
        "service": "kafka",
        "instance_id": instance_id,
        "volumes_removed": remove_volumes,
        "images_removed": remove_images,
        "networks_removed": remove_networks
    }


@activity.defn(name="get_kafka_status_activity")
async def get_kafka_status_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(
        str(KAFKA_YAML),
        instance_id=instance_id,
        env_vars=_build_env(instance_id, params),
    )
    
    status = manager.get_status()
    
    return {
        "service": "kafka",
        "instance_id": instance_id,
        "status": status.value,
        "is_running": status.value == "running"
    }
