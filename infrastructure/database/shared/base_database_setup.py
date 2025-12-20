import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from temporalio import activity

from infrastructure.orchestrator.activities.network.certificate_manage_activity import (
    generate_certificates_activity,
    verify_certificates_activity,
)
from infrastructure.orchestrator.activities.network.host_manage_activity import (
    add_hosts_entries_activity,
    verify_hosts_entries_activity,
)
from infrastructure.orchestrator.base.base_container_activity import YAMLContainerManager, ContainerState
from infrastructure.orchestrator.base.logql_logger import LogQLLogger

logger = logging.getLogger(__name__)

class BaseDatabaseSetupActivity:
    """
    Base class for database setup activities.
    Uses YAMLContainerManager via composition to handle Docker lifecycle.
    """
    
    def __init__(self, service_name: str, compose_file: str, hostname: str, ip: str):
        self.service_name = service_name
        self.compose_file = Path(compose_file)
        self.hostname = hostname
        self.ip = ip
        self.log = LogQLLogger(f"{__name__}.{self.__class__.__name__}")
        self.trace_id = self.log.set_trace_id()

    async def setup_service(self, env_vars: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Orchestrates the setup of a database service.
        Note: Network, Certs, and Hosts are handled by the Workflow before calling this.
        This method focuses on converting the Compose file and running the container.
        """
        start_time = time.time()
        
        self.log.info(
            "setup_service_start", 
            service=self.service_name, 
            hostname=self.hostname, 
            ip=self.ip
        )

        try:
            if not self.compose_file.exists():
                raise FileNotFoundError(f"Compose file not found: {self.compose_file}")

            await self._ensure_prerequisites(env_vars or {})

            manager = YAMLContainerManager(
                yaml_path=str(self.compose_file),
                instance_id=0,
                env_vars=env_vars or {}
            )

            manager.stop(force=True)
            manager.delete(remove_volumes=False)

            success = manager.start(restart_if_running=True)
            
            if not success:
                status = manager.get_status()
                self.log.warning(
                    "container_started_but_not_healthy",
                    service=self.service_name,
                    status=status.value
                )
                
                if status.value in ["running", "unknown"]:
                    self.log.info(
                        "container_running_accepting_unknown_state",
                        service=self.service_name,
                        status=status.value
                    )
                    success = True
                else:
                    raise Exception(f"Failed to start service: {self.service_name}")

            status = manager.get_status()
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            self.log.info(
                "setup_service_complete",
                service=self.service_name,
                duration_ms=duration_ms,
                status=status.value
            )

            return {
                "success": True,
                "service": self.service_name,
                "hostname": self.hostname,
                "ip": self.ip,
                "status": status.value,
                "duration_ms": duration_ms
            }

        except Exception as e:
            self.log.exception("setup_service_failed", error=e)
            return {
                "success": False,
                "service": self.service_name,
                "error": str(e)
            }

    async def _ensure_prerequisites(self, env_vars: Dict[str, str]) -> None:
        await self._ensure_certificates(env_vars)
        await self._ensure_host_entries()

    def _resolve_certs_dir(self, env_vars: Dict[str, str]) -> Path:
        env_value = (env_vars.get("CERTS_DIR") or "").strip()
        if env_value:
            return Path(env_value).expanduser()

        registry_path = (
            Path(__file__).resolve().parents[2]
            / "orchestrator"
            / "activities"
            / "network"
            / "config"
            / "certificate_registry.yaml"
        )

        if registry_path.exists():
            try:
                with registry_path.open("r", encoding="utf-8") as registry_file:
                    registry_data = yaml.safe_load(registry_file) or {}
                cert_entry = registry_data.get(self.hostname)
                if isinstance(cert_entry, dict):
                    cert_file = cert_entry.get("cert_file")
                    if cert_file:
                        return Path(cert_file).expanduser().parent
            except (OSError, yaml.YAMLError) as error:
                self.log.warning(
                    "resolve_certs_dir_registry_read_failed",
                    service=self.service_name,
                    hostname=self.hostname,
                    registry_path=str(registry_path),
                    error=str(error),
                )

        return Path.home() / ".certs"

    async def _ensure_certificates(self, env_vars: Dict[str, str]) -> None:
        certs_dir = self._resolve_certs_dir(env_vars)
        params: Dict[str, Any] = {
            "hostnames": [self.hostname],
            "trace_id": self.trace_id,
            "certs_dir": str(certs_dir),
        }

        self.log.info(
            "ensure_certificates_start",
            service=self.service_name,
            hostname=self.hostname,
            certs_dir=params.get("certs_dir"),
        )

        generate_result = await generate_certificates_activity(params)
        if not generate_result.get("success"):
            raise RuntimeError(
                f"Certificate generation failed for {self.hostname}: {generate_result.get('error') or generate_result.get('results')}"
            )

        verify_params = params.copy()
        verify_result = await verify_certificates_activity(verify_params)

        failed_hosts = [
            host for host, details in verify_result.get("results", {}).items()
            if not details.get("verified")
        ]
        if failed_hosts or not verify_result.get("success"):
            raise RuntimeError(
                f"Certificate verification failed for host(s): {failed_hosts or [self.hostname]}"
            )

        self.log.info(
            "ensure_certificates_complete",
            service=self.service_name,
            hostname=self.hostname,
            certs_dir=params.get("certs_dir"),
        )

    async def _ensure_host_entries(self) -> None:
        params: Dict[str, Any] = {
            "entries": [
                {"hostname": self.hostname, "ip": self.ip}
            ],
            "force_replace": True,
            "trace_id": self.trace_id,
        }

        self.log.info(
            "ensure_hosts_start",
            service=self.service_name,
            hostname=self.hostname,
            ip=self.ip,
        )

        add_result = await add_hosts_entries_activity(params)
        if not add_result.get("success"):
            raise RuntimeError(
                f"Host allocation failed for {self.hostname}: {add_result.get('results')}"
            )

        verify_result = await verify_hosts_entries_activity(
            {"hostnames": [self.hostname], "trace_id": self.trace_id}
        )

        failed_hosts = [
            host for host, details in verify_result.get("results", {}).items()
            if not details.get("verified")
        ]
        if failed_hosts or not verify_result.get("success"):
            raise RuntimeError(
                f"Host verification failed for host(s): {failed_hosts or [self.hostname]}"
            )

        self.log.info(
            "ensure_hosts_complete",
            service=self.service_name,
            hostname=self.hostname,
            ip=self.ip,
        )

    async def teardown_service(self) -> Dict[str, Any]:
        """
        Stops and removes the service container.
        Preserves volumes.
        """
        try:
            manager = YAMLContainerManager(
                yaml_path=str(self.compose_file),
                instance_id=0
            )
            
            stopped = manager.stop(force=True)
            deleted = manager.delete(remove_volumes=False)
            
            return {
                "success": stopped and deleted,
                "service": self.service_name
            }
        except Exception as e:
            self.log.exception("teardown_service_failed", error=e)
            return {
                "success": False,
                "service": self.service_name,
                "error": str(e)
            }   