from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base import YAMLContainerManager

TRAEFIK_YAML = Path(__file__).parent.parent.parent / "config" / "docker" / "traefik-dynamic-docker.yaml"


@activity.defn(name="start_traefik_activity")
async def start_traefik_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(str(TRAEFIK_YAML), instance_id=instance_id)
    
    success = manager.start(restart_if_running=True)
    
    return {
        "success": success,
        "service": "traefik",
        "instance_id": instance_id,
        "status": manager.get_status().value
    }


@activity.defn(name="stop_traefik_activity")
async def stop_traefik_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    force = params.get("force", True)
    manager = YAMLContainerManager(str(TRAEFIK_YAML), instance_id=instance_id)
    
    success = manager.stop(force=force)
    
    return {
        "success": success,
        "service": "traefik",
        "instance_id": instance_id,
        "force": force
    }


@activity.defn(name="restart_traefik_activity")
async def restart_traefik_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(str(TRAEFIK_YAML), instance_id=instance_id)
    
    success = manager.restart()
    
    return {
        "success": success,
        "service": "traefik",
        "instance_id": instance_id,
        "status": manager.get_status().value
    }


@activity.defn(name="delete_traefik_activity")
async def delete_traefik_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    remove_volumes = params.get("remove_volumes", True)
    remove_images = params.get("remove_images", True)
    remove_networks = params.get("remove_networks", False)
    
    manager = YAMLContainerManager(str(TRAEFIK_YAML), instance_id=instance_id)
    
    success = manager.delete(
        remove_volumes=remove_volumes,
        remove_images=remove_images,
        remove_networks=remove_networks
    )
    
    return {
        "success": success,
        "service": "traefik",
        "instance_id": instance_id,
        "volumes_removed": remove_volumes,
        "images_removed": remove_images,
        "networks_removed": remove_networks
    }


@activity.defn(name="get_traefik_status_activity")
async def get_traefik_status_activity(params: dict) -> dict:
    instance_id = params.get("instance_id", 0)
    manager = YAMLContainerManager(str(TRAEFIK_YAML), instance_id=instance_id)
    
    status = manager.get_status()
    
    return {
        "service": "traefik",
        "instance_id": instance_id,
        "status": status.value,
        "is_running": status.value == "running"
    }


@activity.defn(name="verify_traefik_routing_activity")
async def verify_traefik_routing_activity(params: dict) -> dict:
    import requests
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    
    services = params.get("services", [])
    traefik_http_port = params.get("traefik_http_port", 13080)
    trace_id = params.get("trace_id", "traefik-routing-verify")
    
    start_time = time.time()
    results = {}
    all_passed = True
    
    logger.info(
        "event=routing_verification_start trace_id=%s services_count=%d traefik_http_port=%d",
        trace_id, len(services), traefik_http_port
    )
    
    if not services:
        services = [
            {"name": "kafka-ui", "hostname": "scaibu.kafka-ui", "port": 8080},
            {"name": "mongoexpress", "hostname": "scaibu.mongoexpress", "port": 8081},
        ]
    
    for service in services:
        service_name = service.get("name")
        hostname = service.get("hostname")
        
        try:
            url = f"http://localhost:{traefik_http_port}"
            headers = {"Host": hostname}
            
            logger.info(
                "event=routing_test_start trace_id=%s service=%s hostname=%s url=%s",
                trace_id, service_name, hostname, url
            )
            
            response = requests.get(
                url,
                headers=headers,
                timeout=10,
                allow_redirects=False,
                verify=False
            )
            
            routing_ok = response.status_code in [200, 301, 302, 307, 308, 404]
            
            results[service_name] = {
                "hostname": hostname,
                "status_code": response.status_code,
                "routed": routing_ok
            }
            
            if not routing_ok:
                all_passed = False
                logger.warning(
                    "event=routing_test_failed trace_id=%s service=%s hostname=%s status_code=%d",
                    trace_id, service_name, hostname, response.status_code
                )
            else:
                logger.info(
                    "event=routing_test_passed trace_id=%s service=%s hostname=%s status_code=%d",
                    trace_id, service_name, hostname, response.status_code
                )
                
        except requests.exceptions.Timeout:
            all_passed = False
            results[service_name] = {
                "hostname": hostname,
                "status_code": None,
                "routed": False,
                "error": "timeout"
            }
            logger.warning(
                "event=routing_test_timeout trace_id=%s service=%s hostname=%s",
                trace_id, service_name, hostname
            )
            
        except Exception as e:
            all_passed = False
            results[service_name] = {
                "hostname": hostname,
                "status_code": None,
                "routed": False,
                "error": str(e)
            }
            logger.error(
                "event=routing_test_error trace_id=%s service=%s hostname=%s error=%s",
                trace_id, service_name, hostname, str(e)
            )
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    logger.info(
        "event=routing_verification_complete trace_id=%s all_passed=%s duration_ms=%d",
        trace_id, all_passed, duration_ms
    )
    
    return {
        "success": all_passed,
        "service": "traefik-routing",
        "results": results,
        "duration_ms": duration_ms,
        "trace_id": trace_id
    }
