from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base import YAMLContainerManager

NEO4J_YAML = Path(__file__).parent.parent.parent / "config" / "docker" / "neo4j-dynamic-docker.yaml"


@activity.defn(name="start_neo4j_activity")
async def start_neo4j_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(str(NEO4J_YAML), instance_id=instance_id)
    
    success = manager.start(restart_if_running=True)
    
    return {
        "success": success,
        "service": "neo4j",
        "instance_id": instance_id,
        "status": manager.get_status().value
    }


@activity.defn(name="stop_neo4j_activity")
async def stop_neo4j_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    force = params.get("force", True)
    manager = YAMLContainerManager(str(NEO4J_YAML), instance_id=instance_id)
    
    success = manager.stop(force=force)
    
    return {
        "success": success,
        "service": "neo4j",
        "instance_id": instance_id,
        "force": force
    }


@activity.defn(name="restart_neo4j_activity")
async def restart_neo4j_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(str(NEO4J_YAML), instance_id=instance_id)
    
    success = manager.restart()
    
    return {
        "success": success,
        "service": "neo4j",
        "instance_id": instance_id,
        "status": manager.get_status().value
    }


@activity.defn(name="delete_neo4j_activity")
async def delete_neo4j_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    remove_volumes = params.get("remove_volumes", True)
    remove_images = params.get("remove_images", True)
    remove_networks = params.get("remove_networks", False)
    
    manager = YAMLContainerManager(str(NEO4J_YAML), instance_id=instance_id)
    
    success = manager.delete(
        remove_volumes=remove_volumes,
        remove_images=remove_images,
        remove_networks=remove_networks
    )
    
    return {
        "success": success,
        "service": "neo4j",
        "instance_id": instance_id,
        "volumes_removed": remove_volumes,
        "images_removed": remove_images,
        "networks_removed": remove_networks
    }


@activity.defn(name="get_neo4j_status_activity")
async def get_neo4j_status_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(str(NEO4J_YAML), instance_id=instance_id)
    
    status = manager.get_status()
    
    return {
        "service": "neo4j",
        "instance_id": instance_id,
        "status": status.value,
        "is_running": status.value == "running"
    }
