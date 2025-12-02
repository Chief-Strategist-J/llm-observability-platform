from pathlib import Path
from typing import Dict
from temporalio import activity
from infrastructure.orchestrator.base import YAMLContainerManager

MONGODB_YAML = Path(__file__).parent.parent.parent / "config" / "docker" / "mongodb-dynamic-docker.yaml"


def _build_env(instance_id: int, params: dict) -> Dict[str, str]:
    env_overrides = {k: str(v) for k, v in (params.get("env_vars") or {}).items()}
    env_overrides.setdefault("MONGODB_INSTANCE_ID", str(instance_id))

    mappings = {
        "root_username": "MONGODB_ROOT_USERNAME",
        "root_password": "MONGODB_ROOT_PASSWORD",
        "database": "MONGODB_DATABASE",
        "port": "MONGODB_PORT",
        "data_network": "DATA_NETWORK",
        "memory_limit": "MONGODB_MEMORY_LIMIT",
        "memory_reservation": "MONGODB_MEMORY_RESERVATION",
        "cpu_limit": "MONGODB_CPU_LIMIT",
        "health_interval": "HEALTH_CHECK_INTERVAL",
        "health_timeout": "HEALTH_CHECK_TIMEOUT",
        "health_retries": "HEALTH_CHECK_RETRIES",
        "health_start_period": "HEALTH_CHECK_START_PERIOD",
    }

    for param_key, env_key in mappings.items():
        if param_key in params and params[param_key] is not None:
            env_overrides[env_key] = str(params[param_key])

    return env_overrides


@activity.defn(name="start_mongodb_activity")
async def start_mongodb_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(
        str(MONGODB_YAML),
        instance_id=instance_id,
        env_vars=_build_env(instance_id, params)
    )
    
    success = manager.start(restart_if_running=True)
    
    return {
        "success": success,
        "service": "mongodb",
        "instance_id": instance_id,
        "status": manager.get_status().value
    }


@activity.defn(name="stop_mongodb_activity")
async def stop_mongodb_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    force = params.get("force", True)
    manager = YAMLContainerManager(
        str(MONGODB_YAML),
        instance_id=instance_id,
        env_vars=_build_env(instance_id, params)
    )
    
    success = manager.stop(force=force)
    
    return {
        "success": success,
        "service": "mongodb",
        "instance_id": instance_id,
        "force": force
    }


@activity.defn(name="restart_mongodb_activity")
async def restart_mongodb_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(
        str(MONGODB_YAML),
        instance_id=instance_id,
        env_vars=_build_env(instance_id, params)
    )
    
    success = manager.restart()
    
    return {
        "success": success,
        "service": "mongodb",
        "instance_id": instance_id,
        "status": manager.get_status().value
    }


@activity.defn(name="delete_mongodb_activity")
async def delete_mongodb_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    remove_volumes = params.get("remove_volumes", True)
    remove_images = params.get("remove_images", True)
    remove_networks = params.get("remove_networks", False)
    
    manager = YAMLContainerManager(
        str(MONGODB_YAML),
        instance_id=instance_id,
        env_vars=_build_env(instance_id, params)
    )
    
    success = manager.delete(
        remove_volumes=remove_volumes,
        remove_images=remove_images,
        remove_networks=remove_networks
    )
    
    return {
        "success": success,
        "service": "mongodb",
        "instance_id": instance_id,
        "volumes_removed": remove_volumes,
        "images_removed": remove_images,
        "networks_removed": remove_networks
    }


@activity.defn(name="get_mongodb_status_activity")
async def get_mongodb_status_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(
        str(MONGODB_YAML),
        instance_id=instance_id,
        env_vars=_build_env(instance_id, params)
    )
    
    status = manager.get_status()
    
    return {
        "service": "mongodb",
        "instance_id": instance_id,
        "status": status.value,
        "is_running": status.value == "running"
    }
