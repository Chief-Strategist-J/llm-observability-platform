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


@activity.defn(name="verify_mongodb_activity")
async def verify_mongodb_activity(params: dict) -> dict:
    import socket
    import subprocess
    import time
    
    instance_id = params.get("instance_id", 0)
    username = params.get("root_username", "admin")
    password = params.get("root_password", "MongoPassword123!")
    trace_id = params.get("trace_id", "mongodb-verify")
    container_name = f"mongodb-instance-{instance_id}"

    
    try:
        cmd_port = ["docker", "inspect", "--format={{(index (index .NetworkSettings.Ports \"27017/tcp\") 0).HostPort}}", container_name]
        result_port = subprocess.run(cmd_port, capture_output=True, text=True, timeout=5)
        if result_port.returncode == 0 and result_port.stdout.strip():
            port = int(result_port.stdout.strip())
        else:
            port = params.get("port", 27017)
    except Exception:
        port = params.get("port", 27017)
    
    start_time = time.time()
    results = {}
    all_passed = True
    
    logger.info(
        "event=verification_start trace_id=%s service=mongodb instance_id=%d port=%d",
        trace_id, instance_id, port
    )
    
    try:
        container_name = f"mongodb-instance-{instance_id}"
        cmd = ["docker", "inspect", "--format={{.State.Health.Status}}", container_name]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        health_status = result.stdout.strip() if result.returncode == 0 else "unknown"
        results["container_health"] = health_status
        
        if health_status != "healthy":
            all_passed = False
            logger.warning(
                "event=health_check_failed trace_id=%s service=mongodb instance_id=%d health_status=%s",
                trace_id, instance_id, health_status
            )
        else:
            logger.info(
                "event=health_check_passed trace_id=%s service=mongodb instance_id=%d health_status=%s",
                trace_id, instance_id, health_status
            )
    except Exception as e:
        all_passed = False
        results["container_health"] = "error"
        logger.error(
            "event=health_check_error trace_id=%s service=mongodb instance_id=%d error=%s",
            trace_id, instance_id, str(e)
        )
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(("localhost", port))
        sock.close()
        
        port_open = result == 0
        results["port_connectivity"] = port_open
        
        if not port_open:
            all_passed = False
            logger.warning(
                "event=port_check_failed trace_id=%s service=mongodb instance_id=%d port=%d",
                trace_id, instance_id, port
            )
        else:
            logger.info(
                "event=port_check_passed trace_id=%s service=mongodb instance_id=%d port=%d",
                trace_id, instance_id, port
            )
    except Exception as e:
        all_passed = False
        results["port_connectivity"] = False
        logger.error(
            "event=port_check_error trace_id=%s service=mongodb instance_id=%d port=%d error=%s",
            trace_id, instance_id, port, str(e)
        )
    
    try:
        container_name = f"mongodb-instance-{instance_id}"
        cmd = [
            "docker", "exec", container_name,
            "mongosh",
            f"--port={port}",
            "--quiet",
            "--eval", "db.adminCommand('ping')",
            "--username", username,
            "--password", password,
            "--authenticationDatabase", "admin"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        ping_ok = result.returncode == 0 and "ok" in result.stdout.lower()
        results["authentication"] = ping_ok
        
        if not ping_ok:
            all_passed = False
            logger.warning(
                "event=auth_check_failed trace_id=%s service=mongodb instance_id=%d error=%s",
                trace_id, instance_id, result.stderr[:200]
            )
        else:
            logger.info(
                "event=auth_check_passed trace_id=%s service=mongodb instance_id=%d",
                trace_id, instance_id
            )
    except Exception as e:
        all_passed = False
        results["authentication"] = False
        logger.error(
            "event=auth_check_error trace_id=%s service=mongodb instance_id=%d error=%s",
            trace_id, instance_id, str(e)
        )
    
    try:
        container_name = f"mongodb-instance-{instance_id}"
        test_db = f"verification_test"
        test_collection = f"test_{int(time.time())}"
        
        insert_cmd = f"use {test_db}; db.{test_collection}.insertOne({{test: 'verification', timestamp: new Date()}})"
        cmd_insert = [
            "docker", "exec", container_name,
            "mongosh",
            f"--port={port}",
            "--quiet",
            "--eval", insert_cmd,
            "--username", username,
            "--password", password,
            "--authenticationDatabase", "admin"
        ]
        result_insert = subprocess.run(cmd_insert, capture_output=True, text=True, timeout=30)
        
        find_cmd = f"use {test_db}; db.{test_collection}.find({{test: 'verification'}}).count()"
        cmd_find = [
            "docker", "exec", container_name,
            "mongosh",
            f"--port={port}",
            "--quiet",
            "--eval", find_cmd,
            "--username", username,
            "--password", password,
            "--authenticationDatabase", "admin"
        ]
        result_find = subprocess.run(cmd_find, capture_output=True, text=True, timeout=30)
        
        db_ops_ok = result_insert.returncode == 0 and result_find.returncode == 0
        results["database_operations"] = db_ops_ok
        
        if not db_ops_ok:
            all_passed = False
            logger.warning(
                "event=db_ops_check_failed trace_id=%s service=mongodb instance_id=%d test_db=%s",
                trace_id, instance_id, test_db
            )
        else:
            logger.info(
                "event=db_ops_check_passed trace_id=%s service=mongodb instance_id=%d test_db=%s",
                trace_id, instance_id, test_db
            )
            
            drop_cmd = f"use {test_db}; db.{test_collection}.drop()"
            cmd_drop = [
                "docker", "exec", container_name,
                "mongosh",
                f"--port={port}",
                "--quiet",
                "--eval", drop_cmd,
                "--username", username,
                "--password", password,
                "--authenticationDatabase", "admin"
            ]
            subprocess.run(cmd_drop, capture_output=True, text=True, timeout=30)
    except Exception as e:
        all_passed = False
        results["database_operations"] = False
        logger.error(
            "event=db_ops_check_error trace_id=%s service=mongodb instance_id=%d error=%s",
            trace_id, instance_id, str(e)
        )
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    logger.info(
        "event=verification_complete trace_id=%s service=mongodb instance_id=%d all_passed=%s duration_ms=%d",
        trace_id, instance_id, all_passed, duration_ms
    )
    
    return {
        "success": all_passed,
        "service": "mongodb",
        "instance_id": instance_id,
        "results": results,
        "duration_ms": duration_ms,
        "trace_id": trace_id
    }
