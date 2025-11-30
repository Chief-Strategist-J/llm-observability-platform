import os
import subprocess
import time
import yaml
import tempfile
import re
from pathlib import Path
from enum import Enum
from typing import Dict, Optional, List, Any
from dataclasses import dataclass

from .logql_logger import LogQLLogger
from .port_manager import PortManager


class ContainerState(Enum):
    RUNNING = "running"
    EXITED = "exited"
    CREATED = "created"
    RESTARTING = "restarting"
    PAUSED = "paused"
    DEAD = "dead"
    NOT_FOUND = "not_found"
    UNKNOWN = "unknown"


@dataclass
class YAMLContainerConfig:
    yaml_path: Path
    service_name: str
    instance_id: int
    env_file: Optional[Path]
    raw_config: Dict[str, Any]


class YAMLConfigLoader:
    def __init__(self, yaml_path: str, instance_id: int = 0):
        self.yaml_path = Path(yaml_path)
        self.instance_id = instance_id
        self.log = LogQLLogger(f"{__name__}.YAMLConfigLoader")
        self.log.set_trace_id()

    def load(self) -> YAMLContainerConfig:
        start_time = time.time()
        self.log.info("yaml_config_load_start", yaml_path=str(self.yaml_path), instance_id=self.instance_id)

        try:
            if not self.yaml_path.exists():
                self.log.error("yaml_config_not_found", yaml_path=str(self.yaml_path))
                raise FileNotFoundError(f"YAML config not found: {self.yaml_path}")

            with open(self.yaml_path, "r") as f:
                config = yaml.safe_load(f)

            if not config or "services" not in config:
                self.log.error("yaml_config_invalid", yaml_path=str(self.yaml_path), error="No services defined")
                raise ValueError(f"Invalid Docker Compose YAML: {self.yaml_path}")

            service_name = list(config["services"].keys())[0]
            env_file = self.yaml_path.parent.parent.parent / ".env"

            duration = int((time.time() - start_time) * 1000)
            self.log.info(
                "yaml_config_load_complete",
                yaml_path=str(self.yaml_path),
                service_name=service_name,
                instance_id=self.instance_id,
                duration_ms=duration,
            )

            return YAMLContainerConfig(
                yaml_path=self.yaml_path,
                service_name=service_name,
                instance_id=self.instance_id,
                env_file=env_file if env_file.exists() else None,
                raw_config=config,
            )

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.exception("yaml_config_load_failed", error=e, yaml_path=str(self.yaml_path), duration_ms=duration)
            raise


class YAMLContainerManager:
    def __init__(self, yaml_path: str, instance_id: int = 0, env_vars: Optional[Dict[str, str]] = None):
        self.yaml_path = Path(yaml_path)
        self.instance_id = instance_id
        self.env_vars = env_vars or {}

        self.log = LogQLLogger(f"{__name__}.YAMLContainerManager")
        self.trace_id = self.log.set_trace_id()

        loader = YAMLConfigLoader(str(self.yaml_path), instance_id)
        self.config = loader.load()

        self.port_manager = PortManager()

        self.log.info(
            "container_manager_initialized",
            service=self.config.service_name,
            instance_id=self.instance_id,
            yaml_path=str(self.yaml_path),
            trace_id=self.trace_id,
        )

    def _build_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        env[f"{self.config.service_name.upper().replace('-', '_')}_INSTANCE_ID"] = str(self.instance_id)

        for key, value in self.env_vars.items():
            env[key] = value

        self.log.debug(
            "env_variables_prepared",
            service=self.config.service_name,
            instance_id=self.instance_id,
            env_count=len(self.env_vars),
        )

        return env

    def _render_compose_file(self) -> Path:
        with open(self.yaml_path, "r") as f:
            content = f.read()

        env = self._build_env().copy()

        if self.config.env_file and self.config.env_file.exists():
            try:
                with open(self.config.env_file, "r") as ef:
                    for line in ef:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            env.setdefault(k, v)
            except Exception:
                self.log.debug("env_file_parse_failed", path=str(self.config.env_file))

        pattern = re.compile(r"\$\{([^}:]+)(?:\:-(.*?)?)?\}")

        def _repl(match: re.Match) -> str:
            var = match.group(1)
            default = match.group(2) if match.group(2) is not None else ""
            return env.get(var, default)

        rendered = pattern.sub(_repl, content)

        tmp = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml")
        try:
            tmp.write(rendered)
            tmp.flush()
            tmp.close()
            return Path(tmp.name)
        except Exception:
            try:
                tmp.close()
            except Exception:
                pass
            raise

    def _ensure_external_networks(self, rendered_yaml_path: Path):
        try:
            with open(rendered_yaml_path, "r") as f:
                data = yaml.safe_load(f)

            networks = data.get("networks", {})
            for name, cfg in networks.items():
                if isinstance(cfg, dict) and cfg.get("external", False) is True:
                    result = subprocess.run(
                        ["docker", "network", "inspect", name], 
                        capture_output=True, 
                        text=True, 
                        check=False
                    )
                    if result.returncode != 0:
                        self.log.info("creating_external_network", network=name)
                        create_result = subprocess.run(
                            ["docker", "network", "create", name], 
                            capture_output=True, 
                            text=True, 
                            check=False
                        )
                        if create_result.returncode == 0:
                            self.log.info("external_network_created", network=name)
                        else:
                            self.log.warning("external_network_create_failed", network=name, stderr=create_result.stderr)
        except Exception as e:
            self.log.exception("ensure_external_networks_failed", error=e)

    def _find_container_by_name(self, name: str) -> Optional[str]:
        try:
            ps = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{.Names}} {{.ID}}"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            lines = ps.stdout.splitlines() if ps.stdout else []
            for line in lines:
                parts = line.strip().split()
                if not parts:
                    continue
                container_name = parts[0]
                container_id = parts[1] if len(parts) > 1 else None
                if container_name == name or container_name == f"/{name}":
                    return container_id
            return None
        except Exception as e:
            self.log.exception("find_container_by_name_failed", container_name=name, error=e)
            return None

    def _find_containers_using_port(self, port: int) -> List[str]:
        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{.ID}} {{.Ports}}"],
                capture_output=True,
                text=True,
                check=False
            )
            containers = []
            for line in result.stdout.splitlines():
                if f"0.0.0.0:{port}" in line or f":{port}->" in line:
                    container_id = line.split()[0]
                    containers.append(container_id)
            return containers
        except Exception as e:
            self.log.exception("find_containers_using_port_failed", port=port, error=e)
            return []

    def _get_ports_from_compose(self, rendered_yaml_path: Path) -> List[int]:
        try:
            with open(rendered_yaml_path, "r") as f:
                data = yaml.safe_load(f) or {}
            
            ports = []
            services = data.get("services", {}) if isinstance(data, dict) else {}
            for svc, cfg in services.items():
                if not isinstance(cfg, dict):
                    continue
                port_mappings = cfg.get("ports", [])
                for mapping in port_mappings:
                    if isinstance(mapping, str):
                        host_port = mapping.split(":")[0]
                        try:
                            ports.append(int(host_port))
                        except ValueError:
                            pass
            return ports
        except Exception as e:
            self.log.exception("get_ports_from_compose_failed", error=e)
            return []

    def _remove_container(self, container_id: str, reason: str = "conflict") -> bool:
        try:
            self.log.info("removing_container", container_id=container_id, reason=reason)
            rm = subprocess.run(
                ["docker", "rm", "-f", container_id], 
                capture_output=True, 
                text=True, 
                check=False
            )
            if rm.returncode == 0:
                self.log.info("container_removed", container_id=container_id, reason=reason)
                return True
            else:
                self.log.error(
                    "container_remove_failed", 
                    container_id=container_id, 
                    stderr=rm.stderr, 
                    return_code=rm.returncode
                )
                return False
        except Exception as e:
            self.log.exception("container_remove_exception", container_id=container_id, error=e)
            return False

    def _find_container_names_from_compose(self, rendered_yaml_path: Path) -> List[str]:
        try:
            with open(rendered_yaml_path, "r") as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            return []

        names: List[str] = []
        services = data.get("services", {}) if isinstance(data, dict) else {}
        for svc, cfg in services.items():
            if not isinstance(cfg, dict):
                continue
            c_name = cfg.get("container_name")
            if c_name and isinstance(c_name, str):
                names.append(c_name)
        return names

    def _cleanup_conflicts(self, rendered_yaml_path: Path) -> None:
        self.log.info("cleanup_conflicts_start", service=self.config.service_name, instance_id=self.instance_id)
        
        container_names = self._find_container_names_from_compose(rendered_yaml_path)
        for name in container_names:
            container_id = self._find_container_by_name(name)
            if container_id:
                self._remove_container(container_id, reason="name_conflict")
        
        ports = self._get_ports_from_compose(rendered_yaml_path)
        removed_ids = set()
        for port in ports:
            containers = self._find_containers_using_port(port)
            for container_id in containers:
                if container_id not in removed_ids:
                    self._remove_container(container_id, reason="port_conflict")
                    removed_ids.add(container_id)
        
        self.log.info("cleanup_conflicts_complete", service=self.config.service_name, instance_id=self.instance_id)

    def _cleanup_networks(self) -> None:
        try:
            self.log.info("cleanup_networks_start", service=self.config.service_name, instance_id=self.instance_id)
            networks = self.config.raw_config.get("networks", {})
            for network_name, cfg in networks.items():
                if not (isinstance(cfg, dict) and cfg.get("external", False)):
                    result = subprocess.run(
                        ["docker", "network", "rm", network_name], 
                        capture_output=True, 
                        text=True, 
                        check=False
                    )
                    if result.returncode == 0:
                        self.log.info("network_removed", network=network_name)
                    else:
                        self.log.debug("network_removal_skipped", network=network_name, reason=result.stderr)
        except Exception as e:
            self.log.exception("cleanup_networks_failed", error=e)

    def _get_container_logs(self, container_id: str, tail: int = 50) -> str:
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", str(tail), container_id],
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout + result.stderr
        except Exception as e:
            self.log.exception("get_container_logs_failed", container_id=container_id, error=e)
            return ""

    def _wait_for_healthy_state(self, max_wait: int = 30, check_interval: int = 2) -> ContainerState:
        self.log.info("waiting_for_healthy_state", service=self.config.service_name, max_wait=max_wait)
        
        waited = 0
        while waited < max_wait:
            state = self.get_status()
            
            if state == ContainerState.RUNNING:
                self.log.info("container_reached_running_state", service=self.config.service_name, waited_seconds=waited)
                return state
            elif state in [ContainerState.EXITED, ContainerState.DEAD]:
                self.log.error("container_failed_to_start", service=self.config.service_name, state=state.value)
                return state
            elif state == ContainerState.RESTARTING:
                self.log.warning("container_restarting", service=self.config.service_name, waited_seconds=waited)
                
            time.sleep(check_interval)
            waited += check_interval
        
        final_state = self.get_status()
        self.log.warning("container_health_wait_timeout", service=self.config.service_name, final_state=final_state.value)
        return final_state

    def _run_docker_compose(self, args: List[str], check: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess:
        start_time = time.time()
        tmp_path = None

        try:
            tmp_path = self._render_compose_file()
            self._ensure_external_networks(tmp_path)

            if any(arg in ("up", "restart") for arg in args):
                self._cleanup_conflicts(tmp_path)

            cmd = ["docker-compose", "-f", str(tmp_path)]
            cmd.extend(args)
            cmd_str = " ".join(cmd)

            self.log.info(
                "docker_compose_command_start", 
                service=self.config.service_name, 
                instance_id=self.instance_id, 
                command=cmd_str, 
                trace_id=self.trace_id
            )

            result = subprocess.run(
                cmd, 
                env=self._build_env(), 
                capture_output=capture_output, 
                text=True, 
                check=check
            )

            duration = int((time.time() - start_time) * 1000)

            self.log.info(
                "docker_compose_command_success", 
                service=self.config.service_name, 
                instance_id=self.instance_id, 
                command=cmd_str, 
                return_code=result.returncode, 
                duration_ms=duration, 
                trace_id=self.trace_id
            )

            if result.stdout:
                self.log.debug(
                    "docker_compose_stdout", 
                    service=self.config.service_name, 
                    instance_id=self.instance_id, 
                    stdout=result.stdout.strip()
                )

            if result.stderr:
                self.log.debug(
                    "docker_compose_stderr", 
                    service=self.config.service_name, 
                    instance_id=self.instance_id, 
                    stderr=result.stderr.strip()
                )

            return result

        except subprocess.CalledProcessError as e:
            duration = int((time.time() - start_time) * 1000)
            cmd_str = f"docker-compose -f {tmp_path}" if tmp_path else "docker-compose"
            self.log.error(
                "docker_compose_command_failed", 
                service=self.config.service_name, 
                instance_id=self.instance_id, 
                command=cmd_str, 
                return_code=e.returncode, 
                duration_ms=duration, 
                stdout=e.stdout, 
                stderr=e.stderr, 
                trace_id=self.trace_id, 
                error_type=type(e).__name__, 
                error_msg=str(e)
            )
            raise

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            cmd_str = f"docker-compose -f {tmp_path}" if tmp_path else "docker-compose"
            self.log.exception(
                "docker_compose_command_exception", 
                service=self.config.service_name, 
                instance_id=self.instance_id, 
                command=cmd_str, 
                duration_ms=duration, 
                error=e, 
                trace_id=self.trace_id
            )
            raise

        finally:
            if tmp_path and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass

    def get_status(self) -> ContainerState:
        start_time = time.time()

        self.log.info(
            "container_status_check_start", 
            service=self.config.service_name, 
            instance_id=self.instance_id, 
            trace_id=self.trace_id
        )

        try:
            result = self._run_docker_compose(["ps", "-q"], check=False, capture_output=True)

            if not result.stdout.strip():
                duration = int((time.time() - start_time) * 1000)
                self.log.info(
                    "container_status_check_complete", 
                    service=self.config.service_name, 
                    instance_id=self.instance_id, 
                    status=ContainerState.NOT_FOUND.value, 
                    duration_ms=duration
                )
                return ContainerState.NOT_FOUND

            container_id = result.stdout.strip()

            inspect_result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Status}}", container_id], 
                capture_output=True, 
                text=True, 
                check=False
            )

            if inspect_result.returncode == 0:
                status_str = inspect_result.stdout.strip()
                try:
                    state = ContainerState(status_str)
                except ValueError:
                    state = ContainerState.UNKNOWN

                duration = int((time.time() - start_time) * 1000)
                self.log.info(
                    "container_status_check_complete", 
                    service=self.config.service_name, 
                    instance_id=self.instance_id, 
                    container_id=container_id, 
                    status=state.value, 
                    duration_ms=duration, 
                    trace_id=self.trace_id
                )

                return state

            return ContainerState.UNKNOWN

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.exception(
                "container_status_check_failed", 
                service=self.config.service_name, 
                instance_id=self.instance_id, 
                duration_ms=duration, 
                error=e, 
                trace_id=self.trace_id
            )
            return ContainerState.UNKNOWN

    def start(self, restart_if_running: bool = True) -> bool:
        start_time = time.time()

        self.log.info(
            "container_start_requested", 
            service=self.config.service_name, 
            instance_id=self.instance_id, 
            restart_if_running=restart_if_running, 
            trace_id=self.trace_id
        )

        try:
            current_state = self.get_status()

            if current_state == ContainerState.RUNNING:
                if restart_if_running:
                    self.log.info(
                        "container_running_stopping_and_restarting", 
                        service=self.config.service_name, 
                        instance_id=self.instance_id, 
                        trace_id=self.trace_id
                    )
                    self.stop(force=True)
                    self.delete(remove_volumes=False, remove_images=False, remove_networks=False)
                else:
                    self.log.info(
                        "container_already_running_skip", 
                        service=self.config.service_name, 
                        instance_id=self.instance_id, 
                        trace_id=self.trace_id
                    )
                    return True
            elif current_state not in [ContainerState.NOT_FOUND]:
                self.log.info(
                    "container_in_non_running_state_cleaning", 
                    service=self.config.service_name, 
                    instance_id=self.instance_id, 
                    current_state=current_state.value, 
                    trace_id=self.trace_id
                )
                self.delete(remove_volumes=False, remove_images=False, remove_networks=False)

            self._run_docker_compose(["up", "-d"])

            final_state = self._wait_for_healthy_state(max_wait=30, check_interval=2)
            
            if final_state == ContainerState.RESTARTING:
                result = self._run_docker_compose(["ps", "-q"], check=False, capture_output=True)
                if result.stdout.strip():
                    container_id = result.stdout.strip()
                    logs = self._get_container_logs(container_id, tail=100)
                    self.log.error("container_stuck_restarting_logs", service=self.config.service_name, logs=logs)

            duration = int((time.time() - start_time) * 1000)
            success = final_state == ContainerState.RUNNING

            self.log.info(
                "container_start_complete", 
                service=self.config.service_name, 
                instance_id=self.instance_id, 
                initial_state=current_state.value, 
                final_state=final_state.value, 
                success=success, 
                duration_ms=duration, 
                trace_id=self.trace_id
            )

            return success

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.exception(
                "container_start_failed",
                error=e,
                service=self.config.service_name, 
                instance_id=self.instance_id, 
                duration_ms=duration, 
                trace_id=self.trace_id
            )
            return False

    def stop(self, force: bool = True, timeout: int = 10) -> bool:
        start_time = time.time()

        self.log.info(
            "container_stop_requested", 
            service=self.config.service_name, 
            instance_id=self.instance_id, 
            force=force, 
            timeout=timeout, 
            trace_id=self.trace_id
        )

        try:
            current_state = self.get_status()

            if current_state == ContainerState.NOT_FOUND:
                self.log.info(
                    "container_not_found_skip_stop", 
                    service=self.config.service_name, 
                    instance_id=self.instance_id, 
                    trace_id=self.trace_id
                )
                return True

            if force:
                self._run_docker_compose(["kill"])
                self.log.info(
                    "container_force_killed", 
                    service=self.config.service_name, 
                    instance_id=self.instance_id, 
                    trace_id=self.trace_id
                )
            else:
                self._run_docker_compose(["stop", "-t", str(timeout)])
                self.log.info(
                    "container_graceful_stopped", 
                    service=self.config.service_name, 
                    instance_id=self.instance_id, 
                    timeout=timeout, 
                    trace_id=self.trace_id
                )

            time.sleep(1)

            duration = int((time.time() - start_time) * 1000)
            final_state = self.get_status()
            success = final_state in [ContainerState.EXITED, ContainerState.NOT_FOUND]

            self.log.info(
                "container_stop_complete", 
                service=self.config.service_name, 
                instance_id=self.instance_id, 
                initial_state=current_state.value, 
                final_state=final_state.value, 
                force=force, 
                success=success, 
                duration_ms=duration, 
                trace_id=self.trace_id
            )

            return success

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.exception(
                "container_stop_failed", 
                service=self.config.service_name, 
                instance_id=self.instance_id, 
                duration_ms=duration, 
                error=e, 
                trace_id=self.trace_id
            )
            return False

    def restart(self) -> bool:
        start_time = time.time()

        self.log.info(
            "container_restart_requested", 
            service=self.config.service_name, 
            instance_id=self.instance_id, 
            trace_id=self.trace_id
        )

        try:
            current_state = self.get_status()

            self.stop(force=True)
            self.delete(remove_volumes=False, remove_images=False, remove_networks=False)
            
            self._run_docker_compose(["up", "-d"])

            final_state = self._wait_for_healthy_state(max_wait=30, check_interval=2)
            
            if final_state == ContainerState.RESTARTING:
                result = self._run_docker_compose(["ps", "-q"], check=False, capture_output=True)
                if result.stdout.strip():
                    container_id = result.stdout.strip()
                    logs = self._get_container_logs(container_id, tail=100)
                    self.log.error("container_stuck_restarting_after_restart_logs", service=self.config.service_name, logs=logs)

            duration = int((time.time() - start_time) * 1000)
            success = final_state == ContainerState.RUNNING

            self.log.info(
                "container_restart_complete", 
                service=self.config.service_name, 
                instance_id=self.instance_id, 
                initial_state=current_state.value, 
                final_state=final_state.value, 
                success=success, 
                duration_ms=duration, 
                trace_id=self.trace_id
            )

            return success

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.exception(
                "container_restart_failed", 
                service=self.config.service_name, 
                instance_id=self.instance_id, 
                duration_ms=duration, 
                error=e, 
                trace_id=self.trace_id
            )
            return False

    def delete(self, remove_volumes: bool = True, remove_images: bool = True, remove_networks: bool = False) -> bool:
        start_time = time.time()

        self.log.info(
            "container_delete_requested", 
            service=self.config.service_name, 
            instance_id=self.instance_id, 
            remove_volumes=remove_volumes, 
            remove_images=remove_images, 
            remove_networks=remove_networks, 
            trace_id=self.trace_id
        )

        try:
            current_state = self.get_status()

            if current_state not in [ContainerState.NOT_FOUND, ContainerState.EXITED]:
                self.log.info(
                    "container_delete_stopping_first", 
                    service=self.config.service_name, 
                    instance_id=self.instance_id, 
                    current_state=current_state.value, 
                    trace_id=self.trace_id
                )
                self.stop(force=True)

            down_args = ["down"]

            if remove_volumes:
                down_args.append("--volumes")
                self.log.info(
                    "container_delete_removing_volumes", 
                    service=self.config.service_name, 
                    instance_id=self.instance_id, 
                    trace_id=self.trace_id
                )

            if remove_images:
                down_args.append("--rmi")
                down_args.append("all")
                self.log.info(
                    "container_delete_removing_images",
                    service=self.config.service_name,
                    instance_id=self.instance_id,
                    trace_id=self.trace_id
                )

            # run docker-compose down
            self._run_docker_compose(down_args)

            # optional network cleanup
            if remove_networks:
                self.log.info(
                    "container_delete_removing_networks",
                    service=self.config.service_name,
                    instance_id=self.instance_id,
                    trace_id=self.trace_id
                )
                self._cleanup_networks()

            duration = int((time.time() - start_time) * 1000)
            final_state = self.get_status()
            success = final_state == ContainerState.NOT_FOUND

            self.log.info(
                "container_delete_complete",
                service=self.config.service_name,
                instance_id=self.instance_id,
                initial_state=current_state.value,
                final_state=final_state.value,
                volumes_removed=remove_volumes,
                images_removed=remove_images,
                networks_removed=remove_networks,
                success=success,
                duration_ms=duration,
                trace_id=self.trace_id
            )
            return success

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.exception(
                "container_delete_failed",
                service=self.config.service_name,
                instance_id=self.instance_id,
                duration_ms=duration,
                error=e,
                trace_id=self.trace_id
            )
            return False

class YAMLBaseService:
    def __init__(self, yaml_path: str, instance_id: int = 0, env_vars: Optional[Dict[str, str]] = None):
        self.manager = YAMLContainerManager(yaml_path, instance_id, env_vars)
        self.log = LogQLLogger(f"{__name__}.{self.__class__.__name__}")
        self.log.set_trace_id()

    def start(self, restart_if_running: bool = True) -> bool:
        return self.manager.start(restart_if_running)

    def stop(self, force: bool = True, timeout: int = 10) -> bool:
        return self.manager.stop(force, timeout)

    def restart(self) -> bool:
        return self.manager.restart()

    def delete(self, remove_volumes: bool = True, remove_images: bool = True, remove_networks: bool = False) -> bool:
        return self.manager.delete(remove_volumes, remove_images, remove_networks)

    def get_status(self) -> ContainerState:
        return self.manager.get_status()


class BaseContainerManager:
    pass
