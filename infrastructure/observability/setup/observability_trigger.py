from __future__ import annotations

import asyncio
import logging
import subprocess
import time
from pathlib import Path
from typing import Optional, Any

import sys
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from infrastructure.orchestrator.base.service_orchestrator import ServiceConfig, ServiceOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

_tracer = trace.get_tracer(__name__)
_obs: Optional[Any] = None

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def _init_tracing():
    global _obs
    try:
        from infrastructure.observability.scripts.observability_client import ObservabilityClient
        _obs = ObservabilityClient(service_name="observability-trigger")
        logger.info("event=tracing_initialized service=observability-trigger")
    except Exception as e:
        logger.warning("event=tracing_init_failed error=%s", str(e))


observability_config = ServiceConfig(
    compose_file="infrastructure/observability/setup/config/observability-dynamic-docker.yaml",
    hostname="scaibu.grafana",
    service_name="observability",
    network_name="observability-network",
    ip_address="172.28.0.60",
    port="3000",
    subnet="172.28.0.0/16",
    gateway="172.28.0.1",
    health_check_command=["wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/api/health"],
    env_vars={},
    additional_hostnames=[
        "scaibu.prometheus",
        "scaibu.loki", 
        "scaibu.jaeger",
        "scaibu.alertmanager",
        "scaibu.otel"
    ],
    expected_container_name="grafana"
)


def start_temporal_infrastructure() -> bool:
    with _tracer.start_as_current_span("start_temporal_infrastructure") as span:
        compose_path = PROJECT_ROOT / "infrastructure" / "orchestrator" / "config" / "docker" / "temporal" / "temporal-orchestrator-compose.yaml"
        span.set_attribute("compose_path", str(compose_path))
        
        logger.info("event=temporal_start_begin compose_path=%s", compose_path)
        
        if _obs:
            _obs.log_info("Starting Temporal infrastructure", {"compose_path": str(compose_path)})
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_path), "up", "-d"],
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT)
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            span.set_attribute("duration_ms", duration_ms)
            
            if result.returncode != 0:
                span.set_status(Status(StatusCode.ERROR, result.stderr))
                logger.error("event=temporal_start_failed returncode=%d stderr=%s duration_ms=%d",
                           result.returncode, result.stderr[:500], duration_ms)
                if _obs:
                    _obs.log_error("Temporal start failed", {"error": result.stderr[:500]})
                return False
            
            span.set_status(Status(StatusCode.OK))
            logger.info("event=temporal_start_success duration_ms=%d", duration_ms)
            
            if _obs:
                _obs.log_info("Temporal started successfully", {"duration_ms": duration_ms})
                _obs.increment_counter("infrastructure_start_total", 1, {"component": "temporal", "status": "success"})
            
            logger.info("event=temporal_wait_for_ready seconds=15")
            time.sleep(15)
            
            return True
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error("event=temporal_start_exception error=%s duration_ms=%d", str(e), duration_ms)
            if _obs:
                _obs.log_error("Temporal start exception", {"error": str(e)})
            return False


def start_orchestrator_worker() -> Optional[subprocess.Popen]:
    with _tracer.start_as_current_span("start_orchestrator_worker") as span:
        logger.info("event=orchestrator_worker_start_begin")
        
        if _obs:
            _obs.log_info("Starting orchestrator worker")
        
        try:
            process = subprocess.Popen(
                [sys.executable, "-m", "infrastructure.orchestrator.base.docker_orchestrator_worker"],
                cwd=str(PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            span.set_attribute("worker.pid", process.pid)
            logger.info("event=orchestrator_worker_started pid=%d", process.pid)
            
            if _obs:
                _obs.log_info("Orchestrator worker started", {"pid": process.pid})
                _obs.increment_counter("infrastructure_start_total", 1, {"component": "orchestrator_worker", "status": "success"})
            
            logger.info("event=orchestrator_worker_wait seconds=5")
            time.sleep(5)
            
            span.set_status(Status(StatusCode.OK))
            return process
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error("event=orchestrator_worker_start_failed error=%s", str(e))
            if _obs:
                _obs.log_error("Orchestrator worker start failed", {"error": str(e)})
            return None


def ensure_networks() -> bool:
    with _tracer.start_as_current_span("ensure_networks") as span:
        # Map of network name to subnet
        network_config = {
            "cicd-network": "172.20.0.0/16",
            "data-network": "172.21.0.0/16",
            "database-network": "172.22.0.0/16",
            "messaging-network": "172.23.0.0/16",
            "observability-network": "172.28.0.0/16",
            "temporal-network": "172.29.0.0/16"
        }
        
        logger.info("event=network_check_start")
        if _obs:
            _obs.log_info("Ensuring required networks exist with correct subnets")
        
        all_success = True
        
        for network, subnet in network_config.items():
            try:
                # Check existence and subnet
                check_cmd = ["docker", "network", "inspect", network]
                check_result = subprocess.run(check_cmd, capture_output=True, text=True)
                
                recreate = False
                if check_result.returncode == 0:
                    # Network exists, check subnet
                    if subnet not in check_result.stdout:
                        logger.warning("event=network_subnet_mismatch network=%s expected=%s msg='Recreating network'", network, subnet)
                        recreate = True
                else:
                    recreate = True # Does not exist
                
                if recreate:
                    # Delete if exists
                    if check_result.returncode == 0:
                         subprocess.run(["docker", "network", "rm", network], capture_output=True)
                         
                    # Create network
                    logger.info("event=creating_network network=%s subnet=%s", network, subnet)
                    create_cmd = ["docker", "network", "create", "--subnet", subnet, network]
                    create_result = subprocess.run(create_cmd, capture_output=True, text=True)
                    
                    if create_result.returncode != 0:
                        logger.error("event=network_create_failed network=%s error=%s", network, create_result.stderr)
                        all_success = False
                    else:
                        logger.info("event=network_created network=%s", network)
                else:
                    logger.debug("event=network_exists_correctly network=%s", network)
                    
            except Exception as e:
                logger.error("event=network_check_exception network=%s error=%s", network, str(e))
                all_success = False
        
        span.set_attribute("success", all_success)
        if all_success:
            span.set_status(Status(StatusCode.OK))
        else:
            span.set_status(Status(StatusCode.ERROR, "Network setup incomplete"))
        
        return all_success


def start_traefik_infrastructure() -> bool:
    with _tracer.start_as_current_span("start_traefik_infrastructure") as span:
        compose_path = PROJECT_ROOT / "infrastructure" / "orchestrator" / "config" / "docker" / "traefik" / "config" / "traefik-dynamic-docker.yaml"
        span.set_attribute("compose_path", str(compose_path))
        
        logger.info("event=traefik_start_begin compose_path=%s", compose_path)
        
        if _obs:
            _obs.log_info("Starting Traefik infrastructure", {"compose_path": str(compose_path)})
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_path), "up", "-d"],
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT)
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            span.set_attribute("duration_ms", duration_ms)
            
            if result.returncode != 0:
                span.set_status(Status(StatusCode.ERROR, result.stderr))
                logger.error("event=traefik_start_failed returncode=%d stderr=%s duration_ms=%d",
                           result.returncode, result.stderr[:500], duration_ms)
                if _obs:
                    _obs.log_error("Traefik start failed", {"error": result.stderr[:500]})
                return False
            
            span.set_status(Status(StatusCode.OK))
            logger.info("event=traefik_start_success duration_ms=%d", duration_ms)
            
            if _obs:
                _obs.log_info("Traefik started successfully", {"duration_ms": duration_ms})
                _obs.increment_counter("infrastructure_start_total", 1, {"component": "traefik", "status": "success"})
            
            logger.info("event=traefik_wait_for_ready seconds=10")
            time.sleep(10)
            
            return True
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error("event=traefik_start_exception error=%s duration_ms=%d", str(e), duration_ms)
            if _obs:
                _obs.log_error("Traefik start exception", {"error": str(e)})
            return False


def verify_traefik_ready() -> bool:
    with _tracer.start_as_current_span("verify_traefik_ready") as span:
        logger.info("event=traefik_health_check_start")
        
        try:
            cmd = ["docker", "inspect", "--format={{.State.Health.Status}}", "traefik-scaibu"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            status = result.stdout.strip() if result.returncode == 0 else "unknown"
            span.set_attribute("health_status", status)
            
            if status == "healthy":
                logger.info("event=traefik_health_check_passed")
                if _obs:
                    _obs.log_info("Traefik health check passed")
                span.set_status(Status(StatusCode.OK))
                return True
            else:
                logger.warning("event=traefik_health_check_failed status=%s", status)
                if _obs:
                    _obs.log_warning(f"Traefik health check failed: {status}")
                span.set_status(Status(StatusCode.ERROR, f"Health status: {status}"))
                return False
                
        except Exception as e:
            logger.error("event=traefik_health_check_error error=%s", str(e))
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            return False


def verify_temporal_ready() -> bool:
    with _tracer.start_as_current_span("verify_temporal_ready") as span:
        logger.info("event=temporal_health_check_start")
        
        try:
            result = subprocess.run(
                ["docker", "exec", "temporal", "/usr/local/bin/tctl", "--address", "temporal:7233", "cluster", "health"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            healthy = result.returncode == 0
            span.set_attribute("healthy", healthy)
            
            if healthy:
                span.set_status(Status(StatusCode.OK))
                logger.info("event=temporal_health_check_passed")
            else:
                span.set_status(Status(StatusCode.ERROR, "Temporal not healthy"))
                logger.warning("event=temporal_health_check_failed stderr=%s", result.stderr[:200])
            
            return healthy
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            logger.warning("event=temporal_health_check_exception error=%s", str(e))
            return False


async def setup() -> None:
    with _tracer.start_as_current_span("observability_setup") as span:
        span.set_attribute("action", "setup")
        span.set_attribute("service", "observability")
        
        start_time = time.time()
        
        logger.info("event=observability_setup_start")
        
        if _obs:
            _obs.log_info("Starting observability stack setup")
        
        orchestrator = ServiceOrchestrator(
            config=observability_config,
            temporal_host="localhost:7233",
            task_queue="docker-orchestrator-queue"
        )
        
        result = await orchestrator.setup()
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        span.set_attribute("result.success", result.get("success"))
        span.set_attribute("result.workflow_id", result.get("workflow_id", ""))
        span.set_attribute("result.duration_ms", duration_ms)
        
        if result.get("success"):
            span.set_status(Status(StatusCode.OK))
            logger.info("event=observability_setup_complete success=True workflow_id=%s duration_ms=%d",
                       result.get("workflow_id"), duration_ms)
            if _obs:
                _obs.log_info("Observability setup completed", {
                    "workflow_id": result.get("workflow_id"),
                    "duration_ms": duration_ms
                })
        else:
            span.set_status(Status(StatusCode.ERROR, result.get("error", "Unknown error")))
            logger.error("event=observability_setup_failed error=%s duration_ms=%d",
                        result.get("error"), duration_ms)
            if _obs:
                _obs.log_error("Observability setup failed", {"error": result.get("error")})


async def teardown() -> None:
    with _tracer.start_as_current_span("observability_teardown") as span:
        span.set_attribute("action", "teardown")
        span.set_attribute("service", "observability")
        
        logger.info("event=observability_teardown_start")
        
        if _obs:
            _obs.log_info("Starting observability stack teardown")
        
        orchestrator = ServiceOrchestrator(
            config=observability_config,
            temporal_host="localhost:7233",
            task_queue="docker-orchestrator-queue"
        )
        
        result = await orchestrator.teardown()
        
        span.set_attribute("result.success", result.get("success"))
        span.set_attribute("result.workflow_id", result.get("workflow_id", ""))
        
        logger.info("event=observability_teardown_result success=%s workflow_id=%s",
                   result.get("success"), result.get("workflow_id"))


async def full_setup() -> None:
    with _tracer.start_as_current_span("full_infrastructure_setup") as span:
        logger.info("event=full_setup_start")
        
        if _obs:
            _obs.log_info("Starting full infrastructure setup")
        
        span.add_event("Ensuring networks exist")
        if not ensure_networks():
            logger.error("event=full_setup_failed stage=networks")
            return

        span.add_event("Starting Temporal infrastructure")
        temporal_ok = start_temporal_infrastructure()
        if not temporal_ok:
            span.set_status(Status(StatusCode.ERROR, "Temporal failed to start"))
            logger.error("event=full_setup_failed stage=temporal")
            return
        
        span.add_event("Starting orchestrator worker")
        worker_process = start_orchestrator_worker()
        if worker_process is None:
            span.set_status(Status(StatusCode.ERROR, "Worker failed to start"))
            logger.error("event=full_setup_failed stage=orchestrator_worker")
            return
        
        span.add_event("Verifying Temporal readiness")
        if not verify_temporal_ready():
            logger.warning("event=temporal_not_ready_yet msg='Proceeding anyway'")

        span.add_event("Starting Traefik infrastructure")
        if not start_traefik_infrastructure():
            span.set_status(Status(StatusCode.ERROR, "Traefik failed to start"))
            logger.error("event=full_setup_failed stage=traefik")
            return

        span.add_event("Verifying Traefik readiness")
        if not verify_traefik_ready():
            span.set_status(Status(StatusCode.ERROR, "Traefik check failed"))
            logger.warning("event=traefik_verification_failed msg='Traefik may not be ready'")
        
        span.add_event("Running observability setup")
        await setup()
        
        span.set_status(Status(StatusCode.OK))
        logger.info("event=full_setup_complete")
        
        if _obs:
            _obs.log_info("Full infrastructure setup completed")


if __name__ == "__main__":
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else "setup"
    
    _init_tracing()
    
    logger.info("event=trigger_start action=%s", action)
    
    if action == "full-setup":
        asyncio.run(full_setup())
    elif action == "setup":
        asyncio.run(setup())
    elif action == "teardown":
        asyncio.run(teardown())
    elif action == "start-temporal":
        start_temporal_infrastructure()
    elif action == "start-worker":
        start_orchestrator_worker()
    else:
        logger.error("event=unknown_action action=%s valid_actions=full-setup,setup,teardown,start-temporal,start-worker", action)
        sys.exit(1)

