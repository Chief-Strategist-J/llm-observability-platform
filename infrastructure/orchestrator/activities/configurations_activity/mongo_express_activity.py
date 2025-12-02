from pathlib import Path
from typing import Dict
from temporalio import activity
from infrastructure.orchestrator.base import YAMLContainerManager

MONGOEXPRESS_YAML = Path(__file__).parent.parent.parent / "config" / "docker" / "mongoexpress-dynamic-docker.yaml"


def _build_env(instance_id: int, params: dict) -> Dict[str, str]:
    env_overrides = {k: str(v) for k, v in (params.get("env_vars") or {}).items()}
    env_overrides.setdefault("MONGOEXPRESS_INSTANCE_ID", str(instance_id))

    mongodb_instance_id = params.get("mongodb_instance_id", params.get("instance_id", instance_id))
    env_overrides.setdefault("MONGODB_INSTANCE_ID", str(mongodb_instance_id))

    mappings = {
        "port": "MONGOEXPRESS_PORT",
        "mongodb_port": "MONGODB_PORT",
        "root_username": "MONGODB_ROOT_USERNAME",
        "root_password": "MONGODB_ROOT_PASSWORD",
        "mongoexpress_username": "MONGOEXPRESS_ADMIN_USERNAME",
        "mongoexpress_password": "MONGOEXPRESS_ADMIN_PASSWORD",
        "data_network": "DATA_NETWORK",
        "observability_network": "OBSERVABILITY_NETWORK",
        "memory_limit": "MONGOEXPRESS_MEMORY_LIMIT",
        "memory_reservation": "MONGOEXPRESS_MEMORY_RESERVATION",
        "cpu_limit": "MONGOEXPRESS_CPU_LIMIT",
    }

    for param_key, env_key in mappings.items():
        if param_key in params and params[param_key] is not None:
            env_overrides[env_key] = str(params[param_key])

    return env_overrides


@activity.defn(name="start_mongoexpress_activity")
async def start_mongoexpress_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(
        str(MONGOEXPRESS_YAML),
        instance_id=instance_id,
        env_vars=_build_env(instance_id, params)
    )
    
    success = manager.start(restart_if_running=True)
    
    return {
        "success": success,
        "service": "mongoexpress",
        "instance_id": instance_id,
        "status": manager.get_status().value
    }


@activity.defn(name="stop_mongoexpress_activity")
async def stop_mongoexpress_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    force = params.get("force", True)
    manager = YAMLContainerManager(
        str(MONGOEXPRESS_YAML),
        instance_id=instance_id,
        env_vars=_build_env(instance_id, params)
    )
    
    success = manager.stop(force=force)
    
    return {
        "success": success,
        "service": "mongoexpress",
        "instance_id": instance_id,
        "force": force
    }


@activity.defn(name="restart_mongoexpress_activity")
async def restart_mongoexpress_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(
        str(MONGOEXPRESS_YAML),
        instance_id=instance_id,
        env_vars=_build_env(instance_id, params)
    )
    
    success = manager.restart()
    
    return {
        "success": success,
        "service": "mongoexpress",
        "instance_id": instance_id,
        "status": manager.get_status().value
    }


@activity.defn(name="delete_mongoexpress_activity")
async def delete_mongoexpress_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    remove_volumes = params.get("remove_volumes", True)
    remove_images = params.get("remove_images", True)
    remove_networks = params.get("remove_networks", False)
    
    manager = YAMLContainerManager(
        str(MONGOEXPRESS_YAML),
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
        "service": "mongoexpress",
        "instance_id": instance_id,
        "volumes_removed": remove_volumes,
        "images_removed": remove_images,
        "networks_removed": remove_networks
    }


@activity.defn(name="get_mongoexpress_status_activity")
async def get_mongoexpress_status_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(
        str(MONGOEXPRESS_YAML),
        instance_id=instance_id,
        env_vars=_build_env(instance_id, params)
    )
    
    status = manager.get_status()
    
    return {
        "service": "mongoexpress",
        "instance_id": instance_id,
        "status": status.value,
        "is_running": status.value == "running"
    }
