from pathlib import Path
from typing import Dict
from temporalio import activity
from infrastructure.orchestrator.base import YAMLContainerManager

CLICKHOUSE_YAML = Path(__file__).parent.parent.parent / "config" / "docker" / "clickhouse-dynamic-docker.yaml"


def _build_clickhouse_env(instance_id: int, params: dict) -> Dict[str, str]:
    env_overrides = {k: str(v) for k, v in (params.get("env_vars") or {}).items()}
    env_overrides.setdefault("CLICKHOUSE_INSTANCE_ID", str(instance_id))

    mappings = {
        # DB config
        "db": "CLICKHOUSE_DB",
        "user": "CLICKHOUSE_USER",
        "password": "CLICKHOUSE_PASSWORD",
        "access_management": "CLICKHOUSE_ACCESS_MANAGEMENT",

        # Image
        "image_tag": "CLICKHOUSE_IMAGE_TAG",

        # Ports / networking
        "http_port": "CLICKHOUSE_HTTP_PORT",
        "tcp_port": "CLICKHOUSE_TCP_PORT",
        "data_network": "DATA_NETWORK",

        # Resources
        "memory_limit": "CLICKHOUSE_MEMORY_LIMIT",
        "memory_reservation": "CLICKHOUSE_MEMORY_RESERVATION",
        "cpu_limit": "CLICKHOUSE_CPU_LIMIT",

        # Healthcheck
        "health_interval": "HEALTH_CHECK_INTERVAL",
        "health_timeout": "HEALTH_CHECK_TIMEOUT",
        "health_retries": "HEALTH_CHECK_RETRIES",
        "health_start_period": "HEALTH_CHECK_START_PERIOD",

        # Traefik
        "traefik_enabled": "CLICKHOUSE_TRAEFIK_ENABLED",
        "http_host": "CLICKHOUSE_HTTP_HOST",
        "traefik_entrypoint": "TRAEFIK_HTTP_ENTRYPOINT",
    }

    for param_key, env_key in mappings.items():
        if param_key in params and params[param_key] is not None:
            env_overrides[env_key] = str(params[param_key])

    return env_overrides


@activity.defn(name="start_clickhouse_activity")
async def start_clickhouse_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(
        str(CLICKHOUSE_YAML),
        instance_id=instance_id,
        env_vars=_build_clickhouse_env(instance_id, params),
    )

    success = manager.start(restart_if_running=True)

    return {
        "success": success,
        "service": "clickhouse",
        "instance_id": instance_id,
        "status": manager.get_status().value,
    }


@activity.defn(name="stop_clickhouse_activity")
async def stop_clickhouse_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    force = params.get("force", True)
    manager = YAMLContainerManager(
        str(CLICKHOUSE_YAML),
        instance_id=instance_id,
        env_vars=_build_clickhouse_env(instance_id, params),
    )

    success = manager.stop(force=force)

    return {
        "success": success,
        "service": "clickhouse",
        "instance_id": instance_id,
        "force": force,
    }


@activity.defn(name="restart_clickhouse_activity")
async def restart_clickhouse_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(
        str(CLICKHOUSE_YAML),
        instance_id=instance_id,
        env_vars=_build_clickhouse_env(instance_id, params),
    )

    success = manager.restart()

    return {
        "success": success,
        "service": "clickhouse",
        "instance_id": instance_id,
        "status": manager.get_status().value,
    }


@activity.defn(name="delete_clickhouse_activity")
async def delete_clickhouse_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    remove_volumes = params.get("remove_volumes", True)
    remove_images = params.get("remove_images", True)
    remove_networks = params.get("remove_networks", False)

    manager = YAMLContainerManager(
        str(CLICKHOUSE_YAML),
        instance_id=instance_id,
        env_vars=_build_clickhouse_env(instance_id, params),
    )

    success = manager.delete(
        remove_volumes=remove_volumes,
        remove_images=remove_images,
        remove_networks=remove_networks,
    )

    return {
        "success": success,
        "service": "clickhouse",
        "instance_id": instance_id,
        "volumes_removed": remove_volumes,
        "images_removed": remove_images,
        "networks_removed": remove_networks,
    }


@activity.defn(name="get_clickhouse_status_activity")
async def get_clickhouse_status_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(
        str(CLICKHOUSE_YAML),
        instance_id=instance_id,
        env_vars=_build_clickhouse_env(instance_id, params),
    )

    status = manager.get_status()

    return {
        "service": "clickhouse",
        "instance_id": instance_id,
        "status": status.value,
        "is_running": status.value == "running",
    }
