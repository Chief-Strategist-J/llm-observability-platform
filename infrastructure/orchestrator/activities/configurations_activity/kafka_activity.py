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


@activity.defn(name="verify_kafka_activity")
async def verify_kafka_activity(params: dict) -> dict:
    import socket
    import subprocess
    import time
    import json
    
    instance_id = params.get("instance_id", 0)
    trace_id = params.get("trace_id", "kafka-verify")
    container_name = f"kafka-instance-{instance_id}"
    
    # Dynamic port discovery
    try:
        cmd_port = ["docker", "inspect", "--format={{(index (index .NetworkSettings.Ports \"9093/tcp\") 0).HostPort}}", container_name]
        result_port = subprocess.run(cmd_port, capture_output=True, text=True, timeout=5)
        if result_port.returncode == 0 and result_port.stdout.strip():
            broker_port = int(result_port.stdout.strip())
        else:
            broker_port = params.get("broker_port", 9093)
    except Exception:
        broker_port = params.get("broker_port", 9093)

    start_time = time.time()
    results = {}
    all_passed = True
    
    logger.info(
        "event=verification_start trace_id=%s service=kafka instance_id=%d broker_port=%d",
        trace_id, instance_id, broker_port
    )
    
    try:
        container_name = f"kafka-instance-{instance_id}"
        cmd = ["docker", "inspect", "--format={{.State.Health.Status}}", container_name]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        health_status = result.stdout.strip() if result.returncode == 0 else "unknown"
        results["container_health"] = health_status
        
        if health_status != "healthy":
            all_passed = False
            logger.warning(
                "event=health_check_failed trace_id=%s service=kafka instance_id=%d health_status=%s",
                trace_id, instance_id, health_status
            )
        else:
            logger.info(
                "event=health_check_passed trace_id=%s service=kafka instance_id=%d health_status=%s",
                trace_id, instance_id, health_status
            )
    except Exception as e:
        all_passed = False
        results["container_health"] = "error"
        logger.error(
            "event=health_check_error trace_id=%s service=kafka instance_id=%d error=%s",
            trace_id, instance_id, str(e)
        )
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(("localhost", broker_port))
        sock.close()
        
        port_open = result == 0
        results["port_connectivity"] = port_open
        
        if not port_open:
            all_passed = False
            logger.warning(
                "event=port_check_failed trace_id=%s service=kafka instance_id=%d port=%d",
                trace_id, instance_id, broker_port
            )
        else:
            logger.info(
                "event=port_check_passed trace_id=%s service=kafka instance_id=%d port=%d",
                trace_id, instance_id, broker_port
            )
    except Exception as e:
        all_passed = False
        results["port_connectivity"] = False
        logger.error(
            "event=port_check_error trace_id=%s service=kafka instance_id=%d port=%d error=%s",
            trace_id, instance_id, broker_port, str(e)
        )
    
    try:
        container_name = f"kafka-instance-{instance_id}"
        cmd = [
            "docker", "exec", container_name,
            "/opt/kafka/bin/kafka-broker-api-versions.sh",
            f"--bootstrap-server=localhost:{broker_port}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        broker_api_ok = result.returncode == 0
        results["broker_api"] = broker_api_ok
        
        if not broker_api_ok:
            all_passed = False
            logger.warning(
                "event=broker_api_check_failed trace_id=%s service=kafka instance_id=%d error=%s",
                trace_id, instance_id, result.stderr[:200]
            )
        else:
            logger.info(
                "event=broker_api_check_passed trace_id=%s service=kafka instance_id=%d",
                trace_id, instance_id
            )
    except Exception as e:
        all_passed = False
        results["broker_api"] = False
        logger.error(
            "event=broker_api_check_error trace_id=%s service=kafka instance_id=%d error=%s",
            trace_id, instance_id, str(e)
        )
    
    try:
        container_name = f"kafka-instance-{instance_id}"
        test_topic = f"verification-test-{int(time.time())}"
        
        cmd_create = [
            "docker", "exec", container_name,
            "/opt/kafka/bin/kafka-topics.sh",
            f"--bootstrap-server=localhost:{broker_port}",
            "--create",
            "--topic", test_topic,
            "--partitions", "1",
            "--replication-factor", "1"
        ]
        result_create = subprocess.run(cmd_create, capture_output=True, text=True, timeout=30)
        
        cmd_list = [
            "docker", "exec", container_name,
            "/opt/kafka/bin/kafka-topics.sh",
            f"--bootstrap-server=localhost:{broker_port}",
            "--list"
        ]
        result_list = subprocess.run(cmd_list, capture_output=True, text=True, timeout=30)
        
        topic_test_ok = result_create.returncode == 0 and test_topic in result_list.stdout
        results["topic_operations"] = topic_test_ok
        
        if not topic_test_ok:
            all_passed = False
            logger.warning(
                "event=topic_test_failed trace_id=%s service=kafka instance_id=%d test_topic=%s",
                trace_id, instance_id, test_topic
            )
        else:
            logger.info(
                "event=topic_test_passed trace_id=%s service=kafka instance_id=%d test_topic=%s",
                trace_id, instance_id, test_topic
            )
            
            cmd_delete = [
                "docker", "exec", container_name,
                "/opt/kafka/bin/kafka-topics.sh",
                f"--bootstrap-server=localhost:{broker_port}",
                "--delete",
                "--topic", test_topic
            ]
            subprocess.run(cmd_delete, capture_output=True, text=True, timeout=30)
    except Exception as e:
        all_passed = False
        results["topic_operations"] = False
        logger.error(
            "event=topic_test_error trace_id=%s service=kafka instance_id=%d error=%s",
            trace_id, instance_id, str(e)
        )
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    logger.info(
        "event=verification_complete trace_id=%s service=kafka instance_id=%d all_passed=%s duration_ms=%d",
        trace_id, instance_id, all_passed, duration_ms
    )
    
    return {
        "success": all_passed,
        "service": "kafka",
        "instance_id": instance_id,
        "results": results,
        "duration_ms": duration_ms,
        "trace_id": trace_id
    }
