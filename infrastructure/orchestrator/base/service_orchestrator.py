from __future__ import annotations

import time
import asyncio
import logging
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from temporalio.client import Client

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)

_observability_client: Optional[Any] = None

def _get_observability():
    global _observability_client
    if _observability_client is None:
        try:
            from infrastructure.observability.scripts.observability_client import ObservabilityClient
            _observability_client = ObservabilityClient(service_name="service-orchestrator")
            logger.info("event=observability_initialized")
        except Exception as e:
            logger.warning("event=observability_init_failed error=%s", str(e))
    return _observability_client


@dataclass
class ServiceConfig:
    compose_file: str
    hostname: str
    service_name: str
    network_name: str = "database-network"
    ip_address: str = "172.29.0.10"
    port: str = "80"
    subnet: str = "172.29.0.0/16"
    gateway: str = "172.29.0.1"
    health_check_command: List[str] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)
    traefik_compose_path: str = "infrastructure/orchestrator/config/docker/traefik/config/traefik-dynamic-docker.yaml"
    tls_config_dir: str = "infrastructure/orchestrator/config/docker/traefik/config/tls"
    certs_dir: str = "infrastructure/orchestrator/config/docker/traefik/certs"
    additional_networks: List[str] = field(default_factory=lambda: [
        "observability-network", "data-network", "messaging-network", 
        "cicd-network", "temporal-network", "database-network"
    ])
    target_service_for_labels: Optional[str] = None
    tls_strategy: str = "local"
    additional_hostnames: List[str] = field(default_factory=list)
    expected_container_name: Optional[str] = None
    image_name: Optional[str] = None


class ServiceOrchestrator:
    def __init__(
        self,
        config: ServiceConfig,
        temporal_host: str = "localhost:7233",
        task_queue: str = "docker-orchestrator-queue",
        enable_tracing: bool = True
    ):
        self.config = config
        self.temporal_host = temporal_host
        self.task_queue = task_queue
        self._tracer = trace.get_tracer(__name__)
        self._obs = None
        if enable_tracing:
            self._obs = _get_observability()
    
    async def setup(self) -> Dict[str, Any]:
        with self._tracer.start_as_current_span("service_orchestrator_setup") as root_span:
            root_span.set_attribute("service.name", self.config.service_name)
            root_span.set_attribute("service.hostname", self.config.hostname)
            root_span.set_attribute("service.network", self.config.network_name)
            root_span.set_attribute("service.ip_address", self.config.ip_address)
            root_span.set_attribute("service.port", self.config.port)
            root_span.set_attribute("temporal.host", self.temporal_host)
            root_span.set_attribute("temporal.task_queue", self.task_queue)
            
            start_time = time.time()
            
            logger.info(
                "event=setup_start service=%s hostname=%s network=%s ip=%s port=%s temporal_host=%s",
                self.config.service_name, self.config.hostname, self.config.network_name,
                self.config.ip_address, self.config.port, self.temporal_host
            )
            
            if self._obs:
                self._obs.log_info("Setup starting", {
                    "service": self.config.service_name,
                    "hostname": self.config.hostname
                })
            
            try:
                with self._tracer.start_as_current_span("temporal_connect") as conn_span:
                    conn_span.set_attribute("temporal.host", self.temporal_host)
                    logger.info("event=temporal_connect_start host=%s", self.temporal_host)
                    
                    client = await Client.connect(self.temporal_host)
                    
                    conn_span.set_status(Status(StatusCode.OK))
                    logger.info("event=temporal_connect_success host=%s", self.temporal_host)
                
                workflow_id = f"service_setup_{self.config.service_name}_{int(time.time())}"
                
                with self._tracer.start_as_current_span("build_workflow_params") as params_span:
                    workflow_params = {
                        "compose_file": self.config.compose_file,
                        "hostname": self.config.hostname,
                        "service_name": self.config.service_name,
                        "network_name": self.config.network_name,
                        "ip_address": self.config.ip_address,
                        "port": self.config.port,
                        "subnet": self.config.subnet,
                        "gateway": self.config.gateway,
                        "health_check_command": self.config.health_check_command,
                        "env_vars": self.config.env_vars,
                        "traefik_compose_path": self.config.traefik_compose_path,
                        "tls_config_dir": self.config.tls_config_dir,
                        "certs_dir": self.config.certs_dir,
                        "additional_networks": self.config.additional_networks,
                        "target_service": self.config.target_service_for_labels,
                        "tls_strategy": self.config.tls_strategy,
                        "additional_hostnames": self.config.additional_hostnames,
                        "expected_container_name": self.config.expected_container_name,
                        "image_name": self.config.image_name
                    }
                    params_span.set_attribute("workflow.id", workflow_id)
                    params_span.set_attribute("workflow.params_count", len(workflow_params))
                    logger.info("event=workflow_params_built workflow_id=%s param_count=%d", workflow_id, len(workflow_params))
                
                with self._tracer.start_as_current_span("ensure_host_entries") as host_span:
                    logger.info("event=host_entries_check_start hostnames=%s", [self.config.hostname] + self.config.additional_hostnames)
                    self._ensure_host_entries()
                    host_span.set_status(Status(StatusCode.OK))
                    logger.info("event=host_entries_check_complete")
                
                with self._tracer.start_as_current_span("start_workflow") as wf_span:
                    wf_span.set_attribute("workflow.id", workflow_id)
                    wf_span.set_attribute("workflow.task_queue", self.task_queue)
                    
                    logger.info("event=workflow_start_begin workflow_id=%s task_queue=%s", workflow_id, self.task_queue)
                    
                    from infrastructure.orchestrator.base.workflows import ServiceSetupWorkflow
                    result = await client.start_workflow(
                        ServiceSetupWorkflow.run,
                        args=[workflow_params],
                        id=workflow_id,
                        task_queue=self.task_queue,
                    )
                    
                    wf_span.set_attribute("workflow.result_id", result.id)
                    wf_span.set_status(Status(StatusCode.OK))
                    logger.info("event=workflow_started workflow_id=%s result_id=%s", workflow_id, result.id)
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                root_span.set_attribute("result.success", True)
                root_span.set_attribute("result.workflow_id", result.id)
                root_span.set_attribute("result.duration_ms", duration_ms)
                root_span.set_status(Status(StatusCode.OK))
                
                logger.info(
                    "event=setup_complete service=%s workflow_id=%s duration_ms=%d",
                    self.config.service_name, result.id, duration_ms
                )
                
                if self._obs:
                    self._obs.log_info("Setup completed successfully", {
                        "service": self.config.service_name,
                        "workflow_id": result.id,
                        "duration_ms": duration_ms
                    })
                    self._obs.increment_counter("orchestrator_setup_total", 1, {
                        "service": self.config.service_name,
                        "status": "success"
                    })
                    self._obs.record_histogram("orchestrator_setup_duration_ms", duration_ms, {
                        "service": self.config.service_name
                    })
                
                return {"success": True, "workflow_id": result.id, "service_name": self.config.service_name, "duration_ms": duration_ms}
                
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                
                root_span.set_attribute("result.success", False)
                root_span.set_attribute("result.error", str(e))
                root_span.set_attribute("result.duration_ms", duration_ms)
                root_span.set_status(Status(StatusCode.ERROR, str(e)))
                root_span.record_exception(e)
                
                logger.error(
                    "event=setup_failed service=%s error=%s error_type=%s duration_ms=%d",
                    self.config.service_name, str(e), type(e).__name__, duration_ms
                )
                
                if self._obs:
                    self._obs.log_error("Setup failed", {
                        "service": self.config.service_name,
                        "error": str(e),
                        "error_type": type(e).__name__
                    })
                    self._obs.increment_counter("orchestrator_setup_total", 1, {
                        "service": self.config.service_name,
                        "status": "error"
                    })
                
                return {"success": False, "error": str(e), "duration_ms": duration_ms}

    def _ensure_host_entries(self) -> None:
        with self._tracer.start_as_current_span("host_entries_update") as span:
            hostnames = [self.config.hostname] + self.config.additional_hostnames
            target_ip = "127.0.2.1"
            span.set_attribute("hostnames", hostnames)
            span.set_attribute("target_ip", target_ip)
            
            needed_updates = []
            for host in hostnames:
                try:
                    check_cmd = f"grep -E '^[[:space:]]*{target_ip}[[:space:]]+{host}([[:space:]]|$)' /etc/hosts"
                    subprocess.check_call(check_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    logger.info("event=host_entry_exists hostname=%s", host)
                except subprocess.CalledProcessError:
                    needed_updates.append(host)
                    logger.info("event=host_entry_missing hostname=%s", host)
            
            span.set_attribute("updates_needed", len(needed_updates))
            
            if needed_updates:
                logger.info("event=host_entries_update_start hosts=%s", needed_updates)
                for host in needed_updates:
                    try:
                        cmd = f"sudo sed -i '/{host}/d' /etc/hosts && echo '{target_ip} {host}' | sudo tee -a /etc/hosts > /dev/null"
                        subprocess.check_call(cmd, shell=True)
                        logger.info("event=host_entry_added hostname=%s target_ip=%s", host, target_ip)
                    except subprocess.CalledProcessError as e:
                        logger.error("event=host_entry_add_failed hostname=%s error=%s", host, str(e))
                        span.record_exception(e)
    
    async def teardown(self) -> Dict[str, Any]:
        with self._tracer.start_as_current_span("service_orchestrator_teardown") as root_span:
            root_span.set_attribute("service.name", self.config.service_name)
            root_span.set_attribute("temporal.host", self.temporal_host)
            
            start_time = time.time()
            
            logger.info("event=teardown_start service=%s", self.config.service_name)
            
            if self._obs:
                self._obs.log_info("Teardown starting", {"service": self.config.service_name})
            
            try:
                with self._tracer.start_as_current_span("temporal_connect") as conn_span:
                    logger.info("event=temporal_connect_start host=%s", self.temporal_host)
                    client = await Client.connect(self.temporal_host)
                    conn_span.set_status(Status(StatusCode.OK))
                    logger.info("event=temporal_connect_success")
                
                workflow_id = f"service_teardown_{self.config.service_name}_{int(time.time())}"
                
                with self._tracer.start_as_current_span("build_teardown_params") as params_span:
                    workflow_params = {
                        "compose_file": self.config.compose_file,
                        "service_name": self.config.service_name,
                        "container_name": self.config.expected_container_name,
                        "image_name": self.config.image_name
                    }
                    params_span.set_attribute("workflow.id", workflow_id)
                    logger.info("event=teardown_params_built workflow_id=%s", workflow_id)
                
                with self._tracer.start_as_current_span("start_teardown_workflow") as wf_span:
                    wf_span.set_attribute("workflow.id", workflow_id)
                    
                    logger.info("event=teardown_workflow_start workflow_id=%s", workflow_id)
                    
                    from infrastructure.orchestrator.base.workflows import ServiceTeardownWorkflow
                    result = await client.start_workflow(
                        ServiceTeardownWorkflow.run,
                        args=[workflow_params],
                        id=workflow_id,
                        task_queue=self.task_queue,
                    )
                    
                    wf_span.set_status(Status(StatusCode.OK))
                    logger.info("event=teardown_workflow_started workflow_id=%s", result.id)
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                root_span.set_attribute("result.success", True)
                root_span.set_attribute("result.workflow_id", result.id)
                root_span.set_attribute("result.duration_ms", duration_ms)
                root_span.set_status(Status(StatusCode.OK))
                
                logger.info("event=teardown_complete service=%s workflow_id=%s duration_ms=%d",
                           self.config.service_name, result.id, duration_ms)
                
                if self._obs:
                    self._obs.log_info("Teardown completed", {
                        "service": self.config.service_name,
                        "workflow_id": result.id
                    })
                    self._obs.increment_counter("orchestrator_teardown_total", 1, {
                        "service": self.config.service_name,
                        "status": "success"
                    })
                
                return {"success": True, "workflow_id": result.id, "service_name": self.config.service_name, "duration_ms": duration_ms}
                
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                
                root_span.set_status(Status(StatusCode.ERROR, str(e)))
                root_span.record_exception(e)
                
                logger.error("event=teardown_failed service=%s error=%s duration_ms=%d",
                            self.config.service_name, str(e), duration_ms)
                
                if self._obs:
                    self._obs.log_error("Teardown failed", {"service": self.config.service_name, "error": str(e)})
                    self._obs.increment_counter("orchestrator_teardown_total", 1, {
                        "service": self.config.service_name,
                        "status": "error"
                    })
                
                return {"success": False, "error": str(e), "duration_ms": duration_ms}

