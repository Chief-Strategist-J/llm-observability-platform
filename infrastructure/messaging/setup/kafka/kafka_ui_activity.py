from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base import YAMLContainerManager

KAFKA_UI_YAML = Path(__file__).parent.parent.parent / "config" / "docker" / "kafka-ui-dynamic-docker.yaml"



def _build_env(instance_id: int, params: dict) -> dict:
    env_overrides = {k: str(v) for k, v in (params.get("env_vars") or {}).items()}
    env_overrides.setdefault("KAFKA_UI_INSTANCE_ID", str(instance_id))
    
    # Force port 8082 to avoid conflict with Temporal UI
    env_overrides.setdefault("SERVER_PORT", "8082")
    env_overrides.setdefault("KAFKA_UI_PORT", "8082")
    
    # Connect to Kafka on port 9094
    kafka_instance_id = params.get("kafka_instance_id", instance_id)
    env_overrides.setdefault("KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS", f"kafka-instance-{kafka_instance_id}:9094")
    
    return env_overrides


@activity.defn(name="start_kafka_ui_activity")
async def start_kafka_ui_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(
        str(KAFKA_UI_YAML), 
        instance_id=instance_id,
        env_vars=_build_env(instance_id, params)
    )
    
    success = manager.start(restart_if_running=True)
    
    return {
        "success": success,
        "service": "kafka-ui",
        "instance_id": instance_id,
        "status": manager.get_status().value
    }


@activity.defn(name="stop_kafka_ui_activity")
async def stop_kafka_ui_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    force = params.get("force", True)
    manager = YAMLContainerManager(
        str(KAFKA_UI_YAML), 
        instance_id=instance_id,
        env_vars=_build_env(instance_id, params)
    )
    
    success = manager.stop(force=force)
    
    return {
        "success": success,
        "service": "kafka-ui",
        "instance_id": instance_id,
        "force": force
    }


@activity.defn(name="restart_kafka_ui_activity")
async def restart_kafka_ui_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(
        str(KAFKA_UI_YAML), 
        instance_id=instance_id,
        env_vars=_build_env(instance_id, params)
    )
    
    success = manager.restart()
    
    return {
        "success": success,
        "service": "kafka-ui",
        "instance_id": instance_id,
        "status": manager.get_status().value
    }


@activity.defn(name="delete_kafka_ui_activity")
async def delete_kafka_ui_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    remove_volumes = params.get("remove_volumes", True)
    remove_images = params.get("remove_images", True)
    remove_networks = params.get("remove_networks", False)
    
    manager = YAMLContainerManager(
        str(KAFKA_UI_YAML), 
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
        "service": "kafka-ui",
        "instance_id": instance_id,
        "volumes_removed": remove_volumes,
        "images_removed": remove_images,
        "networks_removed": remove_networks
    }


@activity.defn(name="get_kafka_ui_status_activity")
async def get_kafka_ui_status_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(
        str(KAFKA_UI_YAML), 
        instance_id=instance_id,
        env_vars=_build_env(instance_id, params)
    )
    
    status = manager.get_status()
    
    return {
        "service": "kafka-ui",
        "instance_id": instance_id,
        "status": status.value,
        "is_running": status.value == "running"
    }
