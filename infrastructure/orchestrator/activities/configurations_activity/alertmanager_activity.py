from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base import YAMLContainerManager

ALERTMANAGER_YAML = Path(__file__).parent.parent.parent / "config" / "docker" / "alertmanager-docker.yaml"


@activity.defn(name="start_alertmanager_activity")
async def start_alertmanager_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(str(ALERTMANAGER_YAML), instance_id=instance_id)
    
    success = manager.start(restart_if_running=True)
    
    return {
        "success": success,
        "service": "alertmanager",
        "instance_id": instance_id,
        "status": manager.get_status().value,
        "url": f"http://scaibu.alertmanager:13101/"
    }


@activity.defn(name="stop_alertmanager_activity")
async def stop_alertmanager_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    force = params.get("force", True)
    manager = YAMLContainerManager(str(ALERTMANAGER_YAML), instance_id=instance_id)
    
    success = manager.stop(force=force)
    
    return {
        "success": success,
        "service": "alertmanager",
        "instance_id": instance_id,
        "force": force
    }


@activity.defn(name="restart_alertmanager_activity")
async def restart_alertmanager_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(str(ALERTMANAGER_YAML), instance_id=instance_id)
    
    success = manager.restart()
    
    return {
        "success": success,
        "service": "alertmanager",
        "instance_id": instance_id,
        "status": manager.get_status().value
    }


@activity.defn(name="delete_alertmanager_activity")
async def delete_alertmanager_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    remove_volumes = params.get("remove_volumes", True)
    remove_images = params.get("remove_images", True)
    remove_networks = params.get("remove_networks", False)
    
    manager = YAMLContainerManager(str(ALERTMANAGER_YAML), instance_id=instance_id)
    
    success = manager.delete(
        remove_volumes=remove_volumes,
        remove_images=remove_images,
        remove_networks=remove_networks
    )
    
    return {
        "success": success,
        "service": "alertmanager",
        "instance_id": instance_id,
        "volumes_removed": remove_volumes,
        "images_removed": remove_images,
        "networks_removed": remove_networks
    }


@activity.defn(name="get_alertmanager_status_activity")
async def get_alertmanager_status_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(str(ALERTMANAGER_YAML), instance_id=instance_id)
    
    status = manager.get_status()
    
    return {
        "service": "alertmanager",
        "instance_id": instance_id,
        "status": status.value,
        "is_running": status.value == "running",
        "url": f"http://scaibu.alertmanager:13101/"
    }
