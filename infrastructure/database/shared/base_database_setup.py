import time
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from opentelemetry import trace
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
from infrastructure.database.shared.database_definitions import (
    TRAEFIK_HOST_IP,
    DATABASE_CONFIG,
    DatabaseNetwork,
    get_host_entries,
    get_all_hostnames,
)


tracer = trace.get_tracer(__name__)


def run_docker_command(cmd: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        return subprocess.CompletedProcess(cmd, 1, "", f"Timeout: {e}")
    except Exception as e:
        return subprocess.CompletedProcess(cmd, 1, "", str(e))


def get_container_logs(container_name: str, tail: int = 100) -> str:
    result = run_docker_command(["docker", "logs", "--tail", str(tail), container_name])
    return result.stdout + result.stderr


def connect_traefik_to_network(network_name: str = "database-network") -> bool:
    check_result = run_docker_command([
        "docker", "network", "inspect", network_name,
        "--format", "{{range .Containers}}{{.Name}}{{end}}"
    ])
    if "traefik-scaibu" in check_result.stdout:
        return True
    
    connect_result = run_docker_command([
        "docker", "network", "connect", network_name, "traefik-scaibu"
    ])
    return connect_result.returncode == 0


def ensure_database_network_exists() -> bool:
    check_result = run_docker_command(["docker", "network", "inspect", DatabaseNetwork.NAME.value])
    if check_result.returncode == 0:
        return True
    
    create_result = run_docker_command([
        "docker", "network", "create",
        "--driver", "bridge",
        "--subnet", DatabaseNetwork.SUBNET.value,
        "--gateway", DatabaseNetwork.GATEWAY.value,
        DatabaseNetwork.NAME.value
    ])
    return create_result.returncode == 0


class BaseDatabaseSetupActivity:
    def __init__(self, service_name: str, compose_file: str, hostname: str, ip: str):
        self.service_name = service_name
        self.compose_file = Path(compose_file)
        self.hostname = hostname
        self.ip = ip
        self.config = DATABASE_CONFIG.get(service_name, {})
        self.hostnames = self.config.get("hostnames", [hostname])
        self.trace_id = f"{service_name}-{int(time.time())}"

    async def setup_service(self, env_vars: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        start_time = time.time()
        
        with tracer.start_as_current_span(f"setup_{self.service_name}") as span:
            span.set_attribute("service.name", self.service_name)
            span.set_attribute("trace_id", self.trace_id)
            span.set_attribute("hostnames", str(self.hostnames))

            try:
                if not self.compose_file.exists():
                    span.set_attribute("error", "compose_file_not_found")
                    raise FileNotFoundError(f"Compose file not found: {self.compose_file}")

                with tracer.start_as_current_span("ensure_network"):
                    if not ensure_database_network_exists():
                        span.set_attribute("error", "network_creation_failed")
                        raise RuntimeError("Failed to create database network")

                with tracer.start_as_current_span("connect_traefik"):
                    connect_traefik_to_network(DatabaseNetwork.NAME.value)

                with tracer.start_as_current_span("ensure_prerequisites"):
                    await self._ensure_prerequisites(env_vars or {})

                with tracer.start_as_current_span("container_lifecycle"):
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
                        span.set_attribute("container_status", status.value)
                        
                        if status.value in ["running", "unknown"]:
                            success = True
                        else:
                            logs = self._get_all_container_logs()
                            span.set_attribute("container_logs", logs[:5000])
                            raise Exception(f"Failed to start {self.service_name}: {logs[:500]}")

                    status = manager.get_status()

                duration_ms = int((time.time() - start_time) * 1000)
                span.set_attribute("duration_ms", duration_ms)
                span.set_attribute("success", True)

                return {
                    "success": True,
                    "service": self.service_name,
                    "hostname": self.hostname,
                    "hostnames": self.hostnames,
                    "ip": self.ip,
                    "status": status.value,
                    "duration_ms": duration_ms,
                    "trace_id": self.trace_id,
                }

            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                span.set_attribute("error", str(e))
                span.set_attribute("duration_ms", duration_ms)
                span.set_attribute("success", False)
                
                logs = self._get_all_container_logs()
                
                return {
                    "success": False,
                    "service": self.service_name,
                    "error": str(e),
                    "container_logs": logs[:5000],
                    "duration_ms": duration_ms,
                    "trace_id": self.trace_id,
                }

    def _get_all_container_logs(self) -> str:
        logs = []
        container_names = [f"{self.service_name}-instance-0"]
        
        with open(self.compose_file, "r") as f:
            try:
                config = yaml.safe_load(f)
                services = config.get("services", {})
                for svc_name, svc_config in services.items():
                    if isinstance(svc_config, dict):
                        container_name = svc_config.get("container_name")
                        if container_name:
                            container_names.append(container_name)
            except Exception:
                pass
        
        for name in set(container_names):
            container_log = get_container_logs(name, tail=50)
            if container_log.strip():
                logs.append(f"=== {name} ===\n{container_log}")
        
        return "\n".join(logs)

    async def _ensure_prerequisites(self, env_vars: Dict[str, str]) -> None:
        with tracer.start_as_current_span("ensure_certificates"):
            await self._ensure_certificates(env_vars)
        
        with tracer.start_as_current_span("ensure_host_entries"):
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
            except (OSError, yaml.YAMLError):
                pass

        return Path.home() / ".certs"

    async def _ensure_certificates(self, env_vars: Dict[str, str]) -> None:
        certs_dir = self._resolve_certs_dir(env_vars)
        params: Dict[str, Any] = {
            "hostnames": self.hostnames,
            "trace_id": self.trace_id,
            "certs_dir": str(certs_dir),
        }

        generate_result = await generate_certificates_activity(params)
        if not generate_result.get("success"):
            raise RuntimeError(
                f"Certificate generation failed for {self.hostnames}: {generate_result.get('error') or generate_result.get('results')}"
            )

        verify_params = params.copy()
        verify_result = await verify_certificates_activity(verify_params)

        failed_hosts = [
            host for host, details in verify_result.get("results", {}).items()
            if not details.get("verified")
        ]
        if failed_hosts or not verify_result.get("success"):
            raise RuntimeError(
                f"Certificate verification failed for: {failed_hosts or self.hostnames}"
            )

    async def _ensure_host_entries(self) -> None:
        entries = get_host_entries(self.service_name)
        if not entries:
            entries = [{"hostname": self.hostname, "ip": TRAEFIK_HOST_IP}]
        
        params: Dict[str, Any] = {
            "entries": entries,
            "force_replace": True,
            "trace_id": self.trace_id,
        }

        add_result = await add_hosts_entries_activity(params)
        if not add_result.get("success"):
            raise RuntimeError(
                f"Host allocation failed for {self.service_name}: {add_result.get('results')}"
            )

        hostnames_to_verify = [e["hostname"] for e in entries]
        verify_result = await verify_hosts_entries_activity(
            {"hostnames": hostnames_to_verify, "trace_id": self.trace_id}
        )

        failed_hosts = [
            host for host, details in verify_result.get("results", {}).items()
            if not details.get("verified")
        ]
        if failed_hosts or not verify_result.get("success"):
            raise RuntimeError(
                f"Host verification failed for: {failed_hosts or hostnames_to_verify}"
            )

    async def teardown_service(self) -> Dict[str, Any]:
        start_time = time.time()
        
        with tracer.start_as_current_span(f"teardown_{self.service_name}") as span:
            span.set_attribute("service.name", self.service_name)
            span.set_attribute("trace_id", self.trace_id)

            try:
                manager = YAMLContainerManager(
                    yaml_path=str(self.compose_file),
                    instance_id=0
                )
                
                logs = self._get_all_container_logs()
                
                stopped = manager.stop(force=True)
                deleted = manager.delete(remove_volumes=False)
                
                duration_ms = int((time.time() - start_time) * 1000)
                success = stopped and deleted
                
                span.set_attribute("stopped", stopped)
                span.set_attribute("deleted", deleted)
                span.set_attribute("success", success)
                span.set_attribute("duration_ms", duration_ms)
                
                return {
                    "success": success,
                    "service": self.service_name,
                    "stopped": stopped,
                    "deleted": deleted,
                    "container_logs": logs[:5000],
                    "duration_ms": duration_ms,
                    "trace_id": self.trace_id,
                }
            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                span.set_attribute("error", str(e))
                span.set_attribute("success", False)
                
                return {
                    "success": False,
                    "service": self.service_name,
                    "error": str(e),
                    "duration_ms": duration_ms,
                    "trace_id": self.trace_id,
                }