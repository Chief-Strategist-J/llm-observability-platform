from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base import YAMLContainerManager

LOKI_YAML = Path(__file__).parent.parent.parent / "config" / "docker" / "loki-dynamic-docker.yaml"


def _get_manager(instance_id: int) -> YAMLContainerManager:
    config_path = Path(__file__).parent.parent.parent / "config" / "loki-config.yaml"
    env_vars = {
        "CONFIG_FILE_PATH": str(config_path.resolve())
    }
    return YAMLContainerManager(str(LOKI_YAML), instance_id=instance_id, env_vars=env_vars)


@activity.defn(name="start_loki_activity")
async def start_loki_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = _get_manager(instance_id)
    
    success = manager.start(restart_if_running=True)
    
    return {
        "success": success,
        "service": "loki",
        "instance_id": instance_id,
        "status": manager.get_status().value
    }


@activity.defn(name="stop_loki_activity")
async def stop_loki_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    force = params.get("force", True)
    manager = _get_manager(instance_id)
    
    success = manager.stop(force=force)
    
    return {
        "success": success,
        "service": "loki",
        "instance_id": instance_id,
        "force": force
    }


@activity.defn(name="restart_loki_activity")
async def restart_loki_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = _get_manager(instance_id)
    
    success = manager.restart()
    
    return {
        "success": success,
        "service": "loki",
        "instance_id": instance_id,
        "status": manager.get_status().value
    }


@activity.defn(name="delete_loki_activity")
async def delete_loki_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    remove_volumes = params.get("remove_volumes", True)
    remove_images = params.get("remove_images", True)
    remove_networks = params.get("remove_networks", False)
    
    manager = _get_manager(instance_id)
    
    success = manager.delete(
        remove_volumes=remove_volumes,
        remove_images=remove_images,
        remove_networks=remove_networks
    )
    
    return {
        "success": success,
        "service": "loki",
        "instance_id": instance_id,
        "volumes_removed": remove_volumes,
        "images_removed": remove_images,
        "networks_removed": remove_networks
    }


@activity.defn(name="get_loki_status_activity")
async def get_loki_status_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = _get_manager(instance_id)
    
    status = manager.get_status()
    
    return {
        "service": "loki",
        "instance_id": instance_id,
        "status": status.value,
        "is_running": status.value == "running"
    }
