from __future__ import annotations

import time
import asyncio
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from temporalio.client import Client

logger = logging.getLogger(__name__)


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
    tls_strategy: str = "local"  # "local" or "acme"
    additional_hostnames: List[str] = field(default_factory=list)
    expected_container_name: Optional[str] = None
    image_name: Optional[str] = None


class ServiceOrchestrator:
    def __init__(
        self,
        config: ServiceConfig,
        temporal_host: str = "localhost:7233",
        task_queue: str = "docker-orchestrator-queue"
    ):
        self.config = config
        self.temporal_host = temporal_host
        self.task_queue = task_queue
    
    async def setup(self) -> Dict[str, Any]:
        try:
            logger.info("event=service_orchestrator_setup_start service=%s hostname=%s", self.config.service_name, self.config.hostname)
            client = await Client.connect(self.temporal_host)
            workflow_id = f"service_setup_{self.config.service_name}_{int(time.time())}"
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
            
            self._ensure_host_entries()
            
            from infrastructure.orchestrator.base.workflows import ServiceSetupWorkflow
            result = await client.start_workflow(
                ServiceSetupWorkflow.run,
                args=[workflow_params],
                id=workflow_id,
                task_queue=self.task_queue,
            )
            logger.info("event=service_orchestrator_setup_workflow_started service=%s workflow_id=%s", self.config.service_name, result.id)
            return {"success": True, "workflow_id": result.id, "service_name": self.config.service_name}
        except Exception as e:
            logger.error("event=service_orchestrator_setup_failed service=%s error=%s", self.config.service_name, str(e))
            return {"success": False, "error": str(e)}

    def _ensure_host_entries(self) -> None:
        import subprocess
        hostnames = [self.config.hostname] + self.config.additional_hostnames
        target_ip = "127.0.2.1"
        
        needed_updates = []
        for host in hostnames:
            try:
                check_cmd = f"grep -E '^[[:space:]]*{target_ip}[[:space:]]+{host}([[:space:]]|$)' /etc/hosts"
                subprocess.check_call(check_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                needed_updates.append(host)
        
        if needed_updates:
            logger.info("event=updating_etc_hosts hosts=%s message='Sudo password may be required'", needed_updates)
            for host in needed_updates:
                try:
                    cmd = f"sudo sed -i '/{host}/d' /etc/hosts && echo '{target_ip} {host}' | sudo tee -a /etc/hosts > /dev/null"
                    subprocess.check_call(cmd, shell=True)
                    logger.info("event=host_entry_updated hostname=%s target=%s", host, target_ip)
                except subprocess.CalledProcessError as e:
                    logger.error("event=host_entry_update_failed hostname=%s error=%s", host, str(e))
    
    async def teardown(self) -> Dict[str, Any]:
        try:
            logger.info("event=service_orchestrator_teardown_start service=%s", self.config.service_name)
            client = await Client.connect(self.temporal_host)
            workflow_id = f"service_teardown_{self.config.service_name}_{int(time.time())}"
            workflow_params = {
                "compose_file": self.config.compose_file,
                "service_name": self.config.service_name,
                "container_name": self.config.expected_container_name,
                "image_name": self.config.image_name
            }
            from infrastructure.orchestrator.base.workflows import ServiceTeardownWorkflow
            result = await client.start_workflow(
                ServiceTeardownWorkflow.run,
                args=[workflow_params],
                id=workflow_id,
                task_queue=self.task_queue,
            )
            logger.info("event=service_orchestrator_teardown_workflow_started service=%s workflow_id=%s", self.config.service_name, result.id)
            return {"success": True, "workflow_id": result.id, "service_name": self.config.service_name}
        except Exception as e:
            logger.error("event=service_orchestrator_teardown_failed service=%s error=%s", self.config.service_name, str(e))
            return {"success": False, "error": str(e)}
