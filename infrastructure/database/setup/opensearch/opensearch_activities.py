from pathlib import Path
from typing import Dict
from temporalio import activity
from infrastructure.orchestrator.base import YAMLContainerManager

OPENSEARCH_YAML = Path(__file__).parent.parent.parent / "config" / "docker" / "opensearch-dynamic-docker.yaml"


def _build_opensearch_env(instance_id: int, params: dict) -> Dict[str, str]:
    env_overrides = {k: str(v) for k, v in (params.get("env_vars") or {}).items()}
    env_overrides.setdefault("OPENSEARCH_INSTANCE_ID", str(instance_id))

    mappings = {
        # Images
        "image_tag": "OPENSEARCH_IMAGE_TAG",
        "dashboards_image_tag": "OPENSEARCH_DASHBOARDS_IMAGE_TAG",

        # Security
        "initial_admin_password": "OPENSEARCH_INITIAL_ADMIN_PASSWORD",
        "security_enabled": "OPENSEARCH_SECURITY_ENABLED",

        # Ports / networking
        "http_port": "OPENSEARCH_HTTP_PORT",
        "metrics_port": "OPENSEARCH_METRICS_PORT",
        "dashboards_http_port": "OPENSEARCH_DASHBOARDS_HTTP_PORT",
        "data_network": "DATA_NETWORK",

        # JVM
        "java_xms": "OPENSEARCH_JAVA_XMS",
        "java_xmx": "OPENSEARCH_JAVA_XMX",

        # Resources
        "memory_limit": "OPENSEARCH_MEMORY_LIMIT",
        "memory_reservation": "OPENSEARCH_MEMORY_RESERVATION",
        "cpu_limit": "OPENSEARCH_CPU_LIMIT",

        "dashboards_memory_limit": "OPENSEARCH_DASHBOARDS_MEMORY_LIMIT",
        "dashboards_memory_reservation": "OPENSEARCH_DASHBOARDS_MEMORY_RESERVATION",
        "dashboards_cpu_limit": "OPENSEARCH_DASHBOARDS_CPU_LIMIT",

        # Healthcheck
        "health_interval": "HEALTH_CHECK_INTERVAL",
        "health_timeout": "HEALTH_CHECK_TIMEOUT",
        "health_retries": "HEALTH_CHECK_RETRIES",
        "health_start_period": "HEALTH_CHECK_START_PERIOD",

        # Traefik
        "traefik_enabled": "OPENSEARCH_TRAEFIK_ENABLED",
        "http_host": "OPENSEARCH_HTTP_HOST",
        "dashboards_traefik_enabled": "OPENSEARCH_DASHBOARDS_TRAEFIK_ENABLED",
        "dashboards_http_host": "OPENSEARCH_DASHBOARDS_HTTP_HOST",
        "traefik_entrypoint": "TRAEFIK_HTTP_ENTRYPOINT",
    }

    for param_key, env_key in mappings.items():
        if param_key in params and params[param_key] is not None:
            env_overrides[env_key] = str(params[param_key])

    return env_overrides


@activity.defn(name="start_opensearch_activity")
async def start_opensearch_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(
        str(OPENSEARCH_YAML),
        instance_id=instance_id,
        env_vars=_build_opensearch_env(instance_id, params),
    )

    success = manager.start(restart_if_running=True)

    return {
        "success": success,
        "service": "opensearch",
        "instance_id": instance_id,
        "status": manager.get_status().value,
    }


@activity.defn(name="stop_opensearch_activity")
async def stop_opensearch_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    force = params.get("force", True)
    manager = YAMLContainerManager(
        str(OPENSEARCH_YAML),
        instance_id=instance_id,
        env_vars=_build_opensearch_env(instance_id, params),
    )

    success = manager.stop(force=force)

    return {
        "success": success,
        "service": "opensearch",
        "instance_id": instance_id,
        "force": force,
    }


@activity.defn(name="restart_opensearch_activity")
async def restart_opensearch_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(
        str(OPENSEARCH_YAML),
        instance_id=instance_id,
        env_vars=_build_opensearch_env(instance_id, params),
    )

    success = manager.restart()

    return {
        "success": success,
        "service": "opensearch",
        "instance_id": instance_id,
        "status": manager.get_status().value,
    }


@activity.defn(name="delete_opensearch_activity")
async def delete_opensearch_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    remove_volumes = params.get("remove_volumes", True)
    remove_images = params.get("remove_images", True)
    remove_networks = params.get("remove_networks", False)

    manager = YAMLContainerManager(
        str(OPENSEARCH_YAML),
        instance_id=instance_id,
        env_vars=_build_opensearch_env(instance_id, params),
    )

    success = manager.delete(
        remove_volumes=remove_volumes,
        remove_images=remove_images,
        remove_networks=remove_networks,
    )

    return {
        "success": success,
        "service": "opensearch",
        "instance_id": instance_id,
        "volumes_removed": remove_volumes,
        "images_removed": remove_images,
        "networks_removed": remove_networks,
    }


@activity.defn(name="get_opensearch_status_activity")
async def get_opensearch_status_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(
        str(OPENSEARCH_YAML),
        instance_id=instance_id,
        env_vars=_build_opensearch_env(instance_id, params),
    )

    status = manager.get_status()

    return {
        "service": "opensearch",
        "instance_id": instance_id,
        "status": status.value,
        "is_running": status.value == "running",
    }
