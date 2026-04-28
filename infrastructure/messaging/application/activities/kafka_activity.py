from pathlib import Path
import logging
from temporalio import activity
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from infrastructure.orchestrator.base import YAMLContainerManager

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)

KAFKA_YAML = Path(__file__).parent.parent.parent / "infrastructure" / "setup" / "config" / "kafka-docker-compose.yaml"



@activity.defn(name="start_kafka_activity")
async def start_kafka_activity(params: dict) -> dict:
    with _tracer.start_as_current_span("start_kafka") as span:
        instance_id = params.get("instance_id", 0)
        span.set_attribute("service", "kafka")
        span.set_attribute("instance_id", instance_id)
        span.set_attribute("action", "start")
        
        logger.info("event=kafka_start_begin instance_id=%d", instance_id)
        
        try:
            with _tracer.start_as_current_span("start_kafka_container") as start_span:
                manager = YAMLContainerManager(str(KAFKA_YAML), instance_id=instance_id)
                success = manager.start(restart_if_running=True)
                status = manager.get_status().value
                start_span.set_attribute("success", success)
                start_span.set_attribute("status", status)
            
            span.set_attribute("result.success", success)
            span.set_attribute("result.status", status)
            
            if success:
                span.set_status(Status(StatusCode.OK))
                logger.info("event=kafka_start_complete instance_id=%d success=True status=%s", instance_id, status)
            else:
                span.set_status(Status(StatusCode.ERROR, "Start failed"))
                logger.error("event=kafka_start_failed instance_id=%d status=%s", instance_id, status)
            
            return {"success": success, "service": "kafka", "instance_id": instance_id, "status": status}
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error("event=kafka_start_exception instance_id=%d error=%s", instance_id, str(e))
            return {"success": False, "service": "kafka", "instance_id": instance_id, "error": str(e)}


@activity.defn(name="stop_kafka_activity")
async def stop_kafka_activity(params: dict) -> dict:
    with _tracer.start_as_current_span("stop_kafka") as span:
        instance_id = params.get("instance_id", 0)
        force = params.get("force", True)
        span.set_attribute("service", "kafka")
        span.set_attribute("instance_id", instance_id)
        span.set_attribute("action", "stop")
        span.set_attribute("force", force)
        
        logger.info("event=kafka_stop_begin instance_id=%d force=%s", instance_id, force)
        
        try:
            manager = YAMLContainerManager(
                str(KAFKA_YAML),
                instance_id=instance_id,
            )
            
            success = manager.stop(force=force)
            
            span.set_attribute("result.success", success)
            
            if success:
                span.set_status(Status(StatusCode.OK))
                logger.info("event=kafka_stop_complete instance_id=%d success=True", instance_id)
            else:
                span.set_status(Status(StatusCode.ERROR, "Stop failed"))
                logger.warning("event=kafka_stop_failed instance_id=%d", instance_id)
            
            return {
                "success": success,
                "service": "kafka",
                "instance_id": instance_id,
                "force": force
            }
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error("event=kafka_stop_exception instance_id=%d error=%s", instance_id, str(e))
            return {"success": False, "service": "kafka", "instance_id": instance_id, "error": str(e)}


@activity.defn(name="restart_kafka_activity")
async def restart_kafka_activity(params: dict) -> dict:
    with _tracer.start_as_current_span("restart_kafka") as span:
        instance_id = params.get("instance_id", 0)
        span.set_attribute("service", "kafka")
        span.set_attribute("instance_id", instance_id)
        span.set_attribute("action", "restart")
        
        logger.info("event=kafka_restart_begin instance_id=%d", instance_id)
        
        try:
            manager = YAMLContainerManager(
                str(KAFKA_YAML),
                instance_id=instance_id,
            )
            
            success = manager.restart()
            status = manager.get_status().value
            
            span.set_attribute("result.success", success)
            span.set_attribute("result.status", status)
            
            if success:
                span.set_status(Status(StatusCode.OK))
                logger.info("event=kafka_restart_complete instance_id=%d success=True status=%s", instance_id, status)
            else:
                span.set_status(Status(StatusCode.ERROR, "Restart failed"))
                logger.error("event=kafka_restart_failed instance_id=%d status=%s", instance_id, status)
            
            return {
                "success": success,
                "service": "kafka",
                "instance_id": instance_id,
                "status": status
            }
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error("event=kafka_restart_exception instance_id=%d error=%s", instance_id, str(e))
            return {"success": False, "service": "kafka", "instance_id": instance_id, "error": str(e)}


@activity.defn(name="delete_kafka_activity")
async def delete_kafka_activity(params: dict) -> dict:
    with _tracer.start_as_current_span("delete_kafka") as span:
        instance_id = params.get("instance_id", 0)
        remove_volumes = params.get("remove_volumes", True)
        remove_images = params.get("remove_images", True)
        remove_networks = params.get("remove_networks", False)
        
        span.set_attribute("service", "kafka")
        span.set_attribute("instance_id", instance_id)
        span.set_attribute("action", "delete")
        span.set_attribute("remove_volumes", remove_volumes)
        span.set_attribute("remove_images", remove_images)
        span.set_attribute("remove_networks", remove_networks)
        
        logger.info("event=kafka_delete_begin instance_id=%d", instance_id)
        
        try:
            manager = YAMLContainerManager(
                str(KAFKA_YAML),
                instance_id=instance_id,
            )
            
            success = manager.delete(
                remove_volumes=remove_volumes,
                remove_images=remove_images,
                remove_networks=remove_networks
            )
            
            span.set_attribute("result.success", success)
            
            if success:
                span.set_status(Status(StatusCode.OK))
                logger.info("event=kafka_delete_complete instance_id=%d success=True", instance_id)
            
            return {
                "success": success,
                "service": "kafka",
                "instance_id": instance_id,
                "volumes_removed": remove_volumes,
                "images_removed": remove_images,
                "networks_removed": remove_networks
            }
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error("event=kafka_delete_exception instance_id=%d error=%s", instance_id, str(e))
            return {"success": False, "service": "kafka", "instance_id": instance_id, "error": str(e)}


@activity.defn(name="get_kafka_status_activity")
async def get_kafka_status_activity(params: dict) -> dict:
    with _tracer.start_as_current_span("get_kafka_status") as span:
        instance_id = params.get("instance_id", 0)
        span.set_attribute("service", "kafka")
        span.set_attribute("instance_id", instance_id)
        span.set_attribute("action", "get_status")
        
        try:
            manager = YAMLContainerManager(
                str(KAFKA_YAML),
                instance_id=instance_id,
            )
            
            status = manager.get_status()
            is_running = status.value == "running"
            
            span.set_attribute("result.status", status.value)
            span.set_attribute("result.is_running", is_running)
            span.set_status(Status(StatusCode.OK))
            
            return {
                "service": "kafka",
                "instance_id": instance_id,
                "status": status.value,
                "is_running": is_running
            }
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error("event=kafka_status_exception instance_id=%d error=%s", instance_id, str(e))
            return {"service": "kafka", "instance_id": instance_id, "status": "error", "is_running": False, "error": str(e)}


@activity.defn(name="verify_kafka_activity")
async def verify_kafka_activity(params: dict) -> dict:
    import socket
    import subprocess
    import time
    
    with _tracer.start_as_current_span("verify_kafka") as span:
        instance_id = params.get("instance_id", 0)
        trace_id = params.get("trace_id", "kafka-verify")
        container_name = f"kafka-instance-{instance_id}"
        
        span.set_attribute("service", "kafka")
        span.set_attribute("instance_id", instance_id)
        span.set_attribute("action", "verify")
        span.set_attribute("trace_id", trace_id)
        
        broker_port = 9093
            

        start_time = time.time()
        results = {}
        all_passed = True
        
        logger.info(
            "event=verification_start trace_id=%s service=kafka instance_id=%d broker_port=%d",
            trace_id, instance_id, broker_port
        )
        
        # 1. Container Health Check
        with _tracer.start_as_current_span("verify_kafka_health") as health_span:
            try:
                cmd = ["docker", "inspect", "--format={{.State.Health.Status}}", container_name]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                health_status = result.stdout.strip() if result.returncode == 0 else "unknown"
                results["container_health"] = health_status
                health_span.set_attribute("health_status", health_status)
                
                if health_status != "healthy":
                    all_passed = False
                    health_span.set_status(Status(StatusCode.ERROR, f"Status: {health_status}"))
                    logger.warning(
                        "event=health_check_failed trace_id=%s service=kafka instance_id=%d health_status=%s",
                        trace_id, instance_id, health_status
                    )
                else:
                    health_span.set_status(Status(StatusCode.OK))
                    logger.info(
                        "event=health_check_passed trace_id=%s service=kafka instance_id=%d health_status=%s",
                        trace_id, instance_id, health_status
                    )
            except Exception as e:
                all_passed = False
                results["container_health"] = "error"
                health_span.record_exception(e)
                health_span.set_status(Status(StatusCode.ERROR, str(e)))
                logger.error(
                    "event=health_check_error trace_id=%s service=kafka instance_id=%d error=%s",
                    trace_id, instance_id, str(e)
                )
        
        # 2. Port Connectivity Check
        with _tracer.start_as_current_span("verify_kafka_port") as port_span:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex(("localhost", broker_port))
                sock.close()
                
                port_open = result == 0
                results["port_connectivity"] = port_open
                port_span.set_attribute("port_open", port_open)
                
                if not port_open:
                    all_passed = False
                    port_span.set_status(Status(StatusCode.ERROR, "Port closed"))
                    logger.warning(
                        "event=port_check_failed trace_id=%s service=kafka instance_id=%d port=%d",
                        trace_id, instance_id, broker_port
                    )
                else:
                    port_span.set_status(Status(StatusCode.OK))
                    logger.info(
                        "event=port_check_passed trace_id=%s service=kafka instance_id=%d port=%d",
                        trace_id, instance_id, broker_port
                    )
            except Exception as e:
                all_passed = False
                results["port_connectivity"] = False
                port_span.record_exception(e)
                port_span.set_status(Status(StatusCode.ERROR, str(e)))
                logger.error(
                    "event=port_check_error trace_id=%s service=kafka instance_id=%d port=%d error=%s",
                    trace_id, instance_id, broker_port, str(e)
                )
        
        # 3. Broker API Versions Check
        with _tracer.start_as_current_span("verify_kafka_api") as api_span:
            try:
                cmd = [
                    "docker", "exec", container_name,
                    "/opt/kafka/bin/kafka-broker-api-versions.sh",
                    f"--bootstrap-server=localhost:{broker_port}"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                broker_api_ok = result.returncode == 0
                results["broker_api"] = broker_api_ok
                api_span.set_attribute("api_ok", broker_api_ok)
                
                if not broker_api_ok:
                    all_passed = False
                    api_span.set_status(Status(StatusCode.ERROR, result.stderr[:200]))
                    logger.warning(
                        "event=broker_api_check_failed trace_id=%s service=kafka instance_id=%d error=%s",
                        trace_id, instance_id, result.stderr[:200]
                    )
                else:
                    api_span.set_status(Status(StatusCode.OK))
                    logger.info(
                        "event=broker_api_check_passed trace_id=%s service=kafka instance_id=%d",
                        trace_id, instance_id
                    )
            except Exception as e:
                all_passed = False
                results["broker_api"] = False
                api_span.record_exception(e)
                api_span.set_status(Status(StatusCode.ERROR, str(e)))
                logger.error(
                    "event=broker_api_check_error trace_id=%s service=kafka instance_id=%d error=%s",
                    trace_id, instance_id, str(e)
                )
        
        # 4. Topic Operations Check
        with _tracer.start_as_current_span("verify_kafka_topics") as topic_span:
            try:
                test_topic = f"verification-test-{int(time.time())}"
                topic_span.set_attribute("test_topic", test_topic)
                
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
                
                if result_create.returncode == 0:
                    topic_span.add_event("topic_created")
                else:
                    topic_span.add_event("topic_creation_failed", {"error": result_create.stderr[:200]})
                
                cmd_list = [
                    "docker", "exec", container_name,
                    "/opt/kafka/bin/kafka-topics.sh",
                    f"--bootstrap-server=localhost:{broker_port}",
                    "--list"
                ]
                result_list = subprocess.run(cmd_list, capture_output=True, text=True, timeout=30)
                
                topic_test_ok = result_create.returncode == 0 and test_topic in result_list.stdout
                results["topic_operations"] = topic_test_ok
                topic_span.set_attribute("topic_ops_ok", topic_test_ok)
                
                if not topic_test_ok:
                    all_passed = False
                    topic_span.set_status(Status(StatusCode.ERROR, "Topic verification failed"))
                    logger.warning(
                        "event=topic_test_failed trace_id=%s service=kafka instance_id=%d test_topic=%s",
                        trace_id, instance_id, test_topic
                    )
                else:
                    topic_span.set_status(Status(StatusCode.OK))
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
                    topic_span.add_event("topic_deleted")
                    
            except Exception as e:
                all_passed = False
                results["topic_operations"] = False
                topic_span.record_exception(e)
                topic_span.set_status(Status(StatusCode.ERROR, str(e)))
                logger.error(
                    "event=topic_test_error trace_id=%s service=kafka instance_id=%d error=%s",
                    trace_id, instance_id, str(e)
                )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        span.set_attribute("result.success", all_passed)
        span.set_attribute("result.duration_ms", duration_ms)
        
        if all_passed:
            span.set_status(Status(StatusCode.OK))
        else:
            span.set_status(Status(StatusCode.ERROR, "One or more verification steps failed"))
        
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
