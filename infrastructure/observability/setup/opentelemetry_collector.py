from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base import YAMLContainerManager

OTEL_COLLECTOR_YAML = Path(__file__).parent.parent.parent / "config" / "docker" / "otel-collector-dynamic-docker.yaml"


def _get_manager(instance_id: int) -> YAMLContainerManager:
    dynamic_dir = Path(__file__).parent.parent.parent / "dynamicconfig"
    env_vars = {
        "OTEL_DYNAMIC_DIR": str(dynamic_dir.resolve())
    }
    return YAMLContainerManager(str(OTEL_COLLECTOR_YAML), instance_id=instance_id, env_vars=env_vars)


@activity.defn(name="start_otel_collector_activity")
async def start_otel_collector_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = _get_manager(instance_id)
    
    success = manager.start(restart_if_running=True)
    
    return {
        "success": success,
        "service": "otel-collector",
        "instance_id": instance_id,
        "status": manager.get_status().value
    }


@activity.defn(name="stop_otel_collector_activity")
async def stop_otel_collector_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    force = params.get("force", True)
    manager = _get_manager(instance_id)
    
    success = manager.stop(force=force)
    
    return {
        "success": success,
        "service": "otel-collector",
        "instance_id": instance_id,
        "force": force
    }


@activity.defn(name="restart_otel_collector_activity")
async def restart_otel_collector_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = _get_manager(instance_id)
    
    success = manager.restart()
    
    return {
        "success": success,
        "service": "otel-collector",
        "instance_id": instance_id,
        "status": manager.get_status().value
    }


@activity.defn(name="delete_otel_collector_activity")
async def delete_otel_collector_activity(params: dict) -> dict:
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
        "service": "otel-collector",
        "instance_id": instance_id,
        "volumes_removed": remove_volumes,
        "images_removed": remove_images,
        "networks_removed": remove_networks
    }


@activity.defn(name="get_otel_collector_status_activity")
async def get_otel_collector_status_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = _get_manager(instance_id)
    
    status = manager.get_status()
    
    return {
        "service": "otel-collector",
        "instance_id": instance_id,
        "status": status.value,
        "is_running": status.value == "running"
    }
