import time
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

import yaml
from opentelemetry import trace
from temporalio import activity

from infrastructure.orchestrator.activities.network.certificate_manage_activity import (
    generate_certificates_activity,
    verify_certificates_activity,
    generate_traefik_tls_config_activity,
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
from infrastructure.orchestrator.base.logql_logger import LogQLLogger


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


def get_container_health(container_name: str) -> str:
    result = run_docker_command(["docker", "inspect", "--format", "{{.State.Health.Status}}", container_name])
    if result.returncode == 0:
        return result.stdout.strip()
    return "none"


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
        self.log = LogQLLogger(f"{__name__}.{service_name}")

    async def setup_service(self, env_vars: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        start_time = time.time()
        
        self.log.set_trace_id(self.trace_id)
        
        with tracer.start_as_current_span(f"setup_{self.service_name}") as span:
            span.set_attribute("service.name", self.service_name)
            span.set_attribute("trace_id", self.trace_id)
            span.set_attribute("hostnames", str(self.hostnames))

            try:
                if not self.compose_file.exists():
                    span.set_attribute("error", "compose_file_not_found")
                    self.log.error(
                        "compose_file_not_found",
                        service=self.service_name,
                        path=str(self.compose_file)
                    )
                    raise FileNotFoundError(f"Compose file not found: {self.compose_file}")

                with tracer.start_as_current_span("ensure_network"):
                    if not ensure_database_network_exists():
                        span.set_attribute("error", "network_creation_failed")
                        self.log.error("network_creation_failed", service=self.service_name)
                        raise RuntimeError("Failed to create database network")

                with tracer.start_as_current_span("connect_traefik"):
                    connect_traefik_to_network(DatabaseNetwork.NAME.value)

                with tracer.start_as_current_span("ensure_prerequisites"):
                    await self._ensure_prerequisites(env_vars or {})

                with tracer.start_as_current_span("pre_pull_images"):
                    self._pre_pull_images()

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
                        
                        logs = self._get_all_container_logs()
                        span.set_attribute("container_logs", logs[:5000])
                        
                        self.log.warning(
                            "container_start_returned_false_checking_health",
                            service=self.service_name,
                            status=status.value
                        )
                        
                        time.sleep(10)
                        
                        if self._wait_for_containers_ready(timeout=180):
                            success = True
                            self.log.info(
                                "containers_became_healthy_after_wait",
                                service=self.service_name
                            )
                        else:
                            self.log.error(
                                "containers_failed_health_checks",
                                service=self.service_name,
                                logs=logs[:1000]
                            )
                            raise Exception(f"Failed to start {self.service_name}: {logs[:500]}")

                    status = manager.get_status()

                duration_ms = int((time.time() - start_time) * 1000)
                span.set_attribute("duration_ms", duration_ms)
                span.set_attribute("success", True)

                self.log.info(
                    "setup_complete",
                    service=self.service_name,
                    success=True,
                    duration_ms=duration_ms,
                    status=status.value
                )

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
                
                self.log.error(
                    "setup_failed",
                    error=e,
                    service=self.service_name,
                    duration_ms=duration_ms,
                    logs=logs[:1000]
                )
                
                return {
                    "success": False,
                    "service": self.service_name,
                    "error": str(e),
                    "container_logs": logs[:5000],
                    "duration_ms": duration_ms,
                    "trace_id": self.trace_id,
                }

    def _pre_pull_images(self) -> bool:
        with open(self.compose_file, "r") as f:
            config = yaml.safe_load(f)
        
        services = config.get("services", {})
        images = []
        
        for service_config in services.values():
            if isinstance(service_config, dict) and "image" in service_config:
                images.append(service_config["image"])
        
        self.log.info(
            "pre_pulling_images",
            service=self.service_name,
            images=images
        )
        
        for image in images:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.log.info(
                        "pulling_image",
                        service=self.service_name,
                        image=image,
                        attempt=attempt + 1
                    )
                    
                    result = subprocess.run(
                        ["docker", "pull", image],
                        capture_output=True,
                        text=True,
                        timeout=180,
                        check=False
                    )
                    
                    if result.returncode == 0:
                        self.log.info(
                            "image_pulled",
                            service=self.service_name,
                            image=image
                        )
                        break
                    else:
                        self.log.warning(
                            "image_pull_failed",
                            service=self.service_name,
                            image=image,
                            attempt=attempt + 1,
                            stderr=result.stderr[:200]
                        )
                        if attempt < max_retries - 1:
                            time.sleep(5)
                        
                except subprocess.TimeoutExpired:
                    self.log.error(
                        "image_pull_timeout",
                        service=self.service_name,
                        image=image,
                        attempt=attempt + 1
                    )
                    if attempt < max_retries - 1:
                        time.sleep(5)
                except Exception as e:
                    self.log.error(
                        "image_pull_exception",
                        error=e,
                        service=self.service_name,
                        image=image
                    )
                    if attempt < max_retries - 1:
                        time.sleep(5)
        
        return True

    def _wait_for_containers_ready(self, timeout: int = 180) -> bool:
        with open(self.compose_file, "r") as f:
            config = yaml.safe_load(f)
        
        services = config.get("services", {})
        container_names = []
        
        for service_config in services.values():
            if isinstance(service_config, dict) and "container_name" in service_config:
                container_names.append(service_config["container_name"])
        
        self.log.info(
            "waiting_for_containers_ready",
            service=self.service_name,
            containers=container_names,
            timeout=timeout
        )
        
        start_time = time.time()
        check_interval = 10
        
        while time.time() - start_time < timeout:
            all_ready = True
            
            for container_name in container_names:
                inspect = run_docker_command([
                    "docker", "inspect", "--format",
                    "{{.State.Status}}:{{.State.Health.Status}}",
                    container_name
                ])
                
                if inspect.returncode == 0:
                    status_parts = inspect.stdout.strip().split(":")
                    container_status = status_parts[0] if len(status_parts) > 0 else "unknown"
                    health_status = status_parts[1] if len(status_parts) > 1 else "none"
                    
                    self.log.info(
                        "container_status_check",
                        service=self.service_name,
                        container=container_name,
                        status=container_status,
                        health=health_status
                    )
                    
                    if container_status != "running":
                        all_ready = False
                        break
                    
                    if health_status not in ("none", "healthy", ""):
                        all_ready = False
                else:
                    all_ready = False
                    break
            
            if all_ready:
                self.log.info(
                    "containers_ready",
                    service=self.service_name,
                    duration=int(time.time() - start_time)
                )
                return True
            
            time.sleep(check_interval)
        
        self.log.warning(
            "containers_ready_timeout",
            service=self.service_name,
            timeout=timeout
        )
        return False

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
            certs_dir = await self._ensure_certificates(env_vars)
        
        with tracer.start_as_current_span("ensure_traefik_tls_config"):
            await self._ensure_traefik_tls_config(certs_dir)
            
        with tracer.start_as_current_span("ensure_host_entries"):
            await self._ensure_host_entries()

    def _resolve_certs_dir(self, env_vars: Dict[str, str]) -> Path:
        env_value = (env_vars.get("CERTS_DIR") or "").strip()
        if env_value:
            return Path(env_value).expanduser()

        # Try to find Traefik certs directory in the project
        project_root = Path(__file__).resolve().parents[2]
        traefik_certs_dir = project_root / "orchestrator" / "config" / "docker" / "traefik" / "certs"
        if traefik_certs_dir.exists():
            return traefik_certs_dir

        return Path.home() / ".certs"

    async def _ensure_certificates(self, env_vars: Dict[str, str]) -> Path:
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
        return certs_dir

    async def _ensure_traefik_tls_config(self, certs_dir: Path) -> None:
        project_root = Path(__file__).resolve().parents[2]
        tls_config_dir = project_root / "orchestrator" / "config" / "docker" / "traefik" / "config" / "tls"
        
        # We assume Traefik mounts /certs from the same volume/path if it's centralized
        # but the activity expects the relative path inside Traefik container
        params = {
            "hostnames": self.hostnames,
            "certs_dir": "/certs",
            "output_file": str(tls_config_dir / f"{self.service_name}_tls.yaml"),
            "trace_id": self.trace_id
        }
        
        result = await generate_traefik_tls_config_activity(params)
        if not result.get("success"):
            raise RuntimeError(f"Traefik TLS config generation failed for {self.service_name}: {result.get('error')}")

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
        
        self.log.set_trace_id(self.trace_id)
        
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
                
                self.log.info(
                    "teardown_complete",
                    service=self.service_name,
                    success=success,
                    duration_ms=duration_ms
                )
                
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
                
                self.log.error(
                    "teardown_failed",
                    error=e,
                    service=self.service_name,
                    duration_ms=duration_ms
                )
                
                return {
                    "success": False,
                    "service": self.service_name,
                    "error": str(e),
                    "duration_ms": duration_ms,
                    "trace_id": self.trace_id,
                }