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


class PodState(Enum):
    RUNNING = "Running"
    PENDING = "Pending"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    UNKNOWN = "Unknown"
    NOT_FOUND = "NotFound"
    TERMINATING = "Terminating"


@dataclass
class YAMLKubernetesConfig:
    yaml_paths: List[Path]
    resource_name: str
    instance_id: int
    namespace: str
    env_file: Optional[Path]
    raw_configs: List[Dict[str, Any]]


class YAMLConfigLoader:
    __slots__ = ('yaml_paths', 'instance_id', 'namespace', 'log', 'trace_id')

    def __init__(self, yaml_paths: List[str], instance_id: int = 0, namespace: str = "default"):
        self.yaml_paths = [Path(p) for p in yaml_paths] if isinstance(yaml_paths, list) else [Path(yaml_paths)]
        self.instance_id = instance_id
        self.namespace = namespace
        self.log = LogQLLogger(f"{__name__}.YAMLConfigLoader")
        self.trace_id = self.log.set_trace_id()

    def load(self) -> YAMLKubernetesConfig:
        start_time = time.time()
        self.log.info("yaml_config_load_start", yaml_count=len(self.yaml_paths), instance_id=self.instance_id, namespace=self.namespace)

        try:
            raw_configs = []
            resource_name = None

            for yaml_path in self.yaml_paths:
                if not yaml_path.exists():
                    self.log.error("yaml_config_not_found", yaml_path=str(yaml_path))
                    raise FileNotFoundError(f"YAML config not found: {yaml_path}")

                with open(yaml_path, "r") as f:
                    config = yaml.safe_load(f)

                if not config:
                    self.log.warning("yaml_config_empty", yaml_path=str(yaml_path))
                    continue

                raw_configs.append(config)

                if resource_name is None and config.get("metadata", {}).get("name"):
                    resource_name = config["metadata"]["name"]

            if not resource_name:
                resource_name = f"resource-{self.instance_id}"

            env_file = self.yaml_paths[0].parent.parent.parent / ".env"

            duration = int((time.time() - start_time) * 1000)
            self.log.info(
                "yaml_config_load_complete",
                resource_name=resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
                configs_loaded=len(raw_configs),
                duration_ms=duration,
            )

            return YAMLKubernetesConfig(
                yaml_paths=self.yaml_paths,
                resource_name=resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
                env_file=env_file if env_file.exists() else None,
                raw_configs=raw_configs,
            )

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.exception("yaml_config_load_failed", error=e, duration_ms=duration)
            raise


class YAMLKubernetesManager:
    __slots__ = ('yaml_paths', 'instance_id', 'namespace', 'env_vars', 'log', 'trace_id', 'config', 'port_manager')

    def __init__(self, yaml_paths: List[str], instance_id: int = 0, namespace: str = "default", env_vars: Optional[Dict[str, str]] = None):
        self.yaml_paths = yaml_paths if isinstance(yaml_paths, list) else [yaml_paths]
        self.instance_id = instance_id
        self.namespace = namespace
        self.env_vars = env_vars or {}

        self.log = LogQLLogger(f"{__name__}.YAMLKubernetesManager")
        self.trace_id = self.log.set_trace_id()

        loader = YAMLConfigLoader(self.yaml_paths, instance_id, namespace)
        self.config = loader.load()

        self.port_manager = PortManager()

        self.log.info(
            "kubernetes_manager_initialized",
            resource=self.config.resource_name,
            instance_id=self.instance_id,
            namespace=self.namespace,
            yaml_count=len(self.yaml_paths),
            trace_id=self.trace_id,
        )

    def _build_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        env["INSTANCE_ID"] = str(self.instance_id)
        env["NAMESPACE"] = self.namespace

        for key, value in self.env_vars.items():
            env[key] = value

        self.log.debug(
            "env_variables_prepared",
            resource=self.config.resource_name,
            instance_id=self.instance_id,
            env_count=len(self.env_vars),
        )

        return env

    def _render_yaml_content(self, yaml_path: Path) -> str:
        with open(yaml_path, "r") as f:
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

        pattern = re.compile(r"\$\{([^}:]+)(?:\:-(.*?))?\}")

        def _repl(match: re.Match) -> str:
            var = match.group(1)
            default = match.group(2) if match.group(2) is not None else ""
            return env.get(var, default)

        rendered = pattern.sub(_repl, content)
        return rendered

    def _render_all_yamls(self) -> Path:
        rendered_contents = []

        for yaml_path in self.config.yaml_paths:
            rendered = self._render_yaml_content(yaml_path)
            rendered_contents.append(rendered)

        combined = "\n---\n".join(rendered_contents)

        tmp = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml")
        try:
            tmp.write(combined)
            tmp.flush()
            tmp.close()
            return Path(tmp.name)
        except Exception:
            try:
                tmp.close()
            except Exception:
                pass
            raise

    def _run_kubectl(self, args: List[str], check: bool = True, capture_output: bool = True) -> subprocess.CompletedProcess:
        start_time = time.time()
        tmp_path = None

        try:
            cmd = ["kubectl"] + args
            cmd_str = " ".join(cmd)

            self.log.info(
                "kubectl_command_start",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
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
                "kubectl_command_success",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
                command=cmd_str,
                return_code=result.returncode,
                duration_ms=duration,
                trace_id=self.trace_id
            )

            if result.stdout:
                self.log.debug(
                    "kubectl_stdout",
                    resource=self.config.resource_name,
                    stdout=result.stdout.strip()
                )

            if result.stderr:
                self.log.debug(
                    "kubectl_stderr",
                    resource=self.config.resource_name,
                    stderr=result.stderr.strip()
                )

            return result

        except subprocess.CalledProcessError as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.error(
                "kubectl_command_failed",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
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
            self.log.exception(
                "kubectl_command_exception",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
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

    def _wait_for_ready_state(self, max_wait: int = 60, check_interval: int = 3) -> PodState:
        self.log.info("waiting_for_ready_state", resource=self.config.resource_name, max_wait=max_wait)

        waited = 0
        while waited < max_wait:
            state = self.get_status()

            if state == PodState.RUNNING:
                self.log.info("pod_reached_running_state", resource=self.config.resource_name, waited_seconds=waited)
                return state
            elif state in [PodState.FAILED]:
                self.log.error("pod_failed_to_start", resource=self.config.resource_name, state=state.value)
                return state

            time.sleep(check_interval)
            waited += check_interval

        final_state = self.get_status()
        self.log.warning("pod_ready_wait_timeout", resource=self.config.resource_name, final_state=final_state.value)
        return final_state

    def get_status(self) -> PodState:
        start_time = time.time()

        self.log.info(
            "pod_status_check_start",
            resource=self.config.resource_name,
            instance_id=self.instance_id,
            namespace=self.namespace,
            trace_id=self.trace_id
        )

        try:
            result = self._run_kubectl(
                [
                    "get", "pods",
                    "-n", self.namespace,
                    "-l", f"instance={self.instance_id}",
                    "-o", "jsonpath={.items[0].status.phase}"
                ],
                check=False,
                capture_output=True
            )

            if not result.stdout.strip():
                duration = int((time.time() - start_time) * 1000)
                self.log.info(
                    "pod_status_check_complete",
                    resource=self.config.resource_name,
                    instance_id=self.instance_id,
                    status=PodState.NOT_FOUND.value,
                    duration_ms=duration
                )
                return PodState.NOT_FOUND

            phase = result.stdout.strip()
            
            try:
                state = PodState(phase)
            except ValueError:
                state = PodState.UNKNOWN

            duration = int((time.time() - start_time) * 1000)
            self.log.info(
                "pod_status_check_complete",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
                status=state.value,
                duration_ms=duration,
                trace_id=self.trace_id
            )

            return state

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.exception(
                "pod_status_check_failed",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
                duration_ms=duration,
                error=e,
                trace_id=self.trace_id
            )
            return PodState.UNKNOWN

    def start(self, restart_if_running: bool = True) -> bool:
        start_time = time.time()

        self.log.info(
            "pod_start_requested",
            resource=self.config.resource_name,
            instance_id=self.instance_id,
            namespace=self.namespace,
            restart_if_running=restart_if_running,
            trace_id=self.trace_id
        )

        try:
            current_state = self.get_status()

            if current_state == PodState.RUNNING:
                if restart_if_running:
                    self.log.info(
                        "pod_running_restarting",
                        resource=self.config.resource_name,
                        instance_id=self.instance_id,
                        trace_id=self.trace_id
                    )
                    self.delete(remove_pvcs=False)
                else:
                    self.log.info(
                        "pod_already_running_skip",
                        resource=self.config.resource_name,
                        instance_id=self.instance_id,
                        trace_id=self.trace_id
                    )
                    return True
            elif current_state not in [PodState.NOT_FOUND]:
                self.log.info(
                    "pod_in_non_running_state_cleaning",
                    resource=self.config.resource_name,
                    instance_id=self.instance_id,
                    current_state=current_state.value,
                    trace_id=self.trace_id
                )
                self.delete(remove_pvcs=False)

            tmp_path = self._render_all_yamls()
            try:
                self._run_kubectl(["apply", "-f", str(tmp_path), "-n", self.namespace])
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()

            final_state = self._wait_for_ready_state(max_wait=60, check_interval=3)

            duration = int((time.time() - start_time) * 1000)
            success = final_state == PodState.RUNNING

            self.log.info(
                "pod_start_complete",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
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
                "pod_start_failed",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
                duration_ms=duration,
                trace_id=self.trace_id,
                error_type=type(e).__name__,
                error_msg=str(e)
            )
            return False

    def stop(self, force: bool = True, timeout: int = 30) -> bool:
        start_time = time.time()

        self.log.info(
            "pod_stop_requested",
            resource=self.config.resource_name,
            instance_id=self.instance_id,
            namespace=self.namespace,
            force=force,
            timeout=timeout,
            trace_id=self.trace_id
        )

        try:
            current_state = self.get_status()

            if current_state == PodState.NOT_FOUND:
                self.log.info(
                    "pod_not_found_skip_stop",
                    resource=self.config.resource_name,
                    instance_id=self.instance_id,
                    trace_id=self.trace_id
                )
                return True

            grace_period = "0" if force else str(timeout)
            
            self._run_kubectl([
                "delete", "deployment,statefulset,pod",
                "-n", self.namespace,
                "-l", f"instance={self.instance_id}",
                f"--grace-period={grace_period}"
            ], check=False)

            self.log.info(
                "pod_stopped",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                force=force,
                trace_id=self.trace_id
            )

            time.sleep(2)

            duration = int((time.time() - start_time) * 1000)
            final_state = self.get_status()
            success = final_state in [PodState.NOT_FOUND, PodState.TERMINATING]

            self.log.info(
                "pod_stop_complete",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
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
                "pod_stop_failed",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
                duration_ms=duration,
                error=e,
                trace_id=self.trace_id
            )
            return False

    def restart(self) -> bool:
        start_time = time.time()

        self.log.info(
            "pod_restart_requested",
            resource=self.config.resource_name,
            instance_id=self.instance_id,
            namespace=self.namespace,
            trace_id=self.trace_id
        )

        try:
            current_state = self.get_status()

            self.stop(force=True)
            time.sleep(2)

            tmp_path = self._render_all_yamls()
            try:
                self._run_kubectl(["apply", "-f", str(tmp_path), "-n", self.namespace])
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()

            final_state = self._wait_for_ready_state(max_wait=60, check_interval=3)

            duration = int((time.time() - start_time) * 1000)
            success = final_state == PodState.RUNNING

            self.log.info(
                "pod_restart_complete",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
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
                "pod_restart_failed",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
                duration_ms=duration,
                error=e,
                trace_id=self.trace_id
            )
            return False

    def delete(self, remove_pvcs: bool = True) -> bool:
        start_time = time.time()

        self.log.info(
            "pod_delete_requested",
            resource=self.config.resource_name,
            instance_id=self.instance_id,
            namespace=self.namespace,
            remove_pvcs=remove_pvcs,
            trace_id=self.trace_id
        )

        try:
            current_state = self.get_status()

            if current_state not in [PodState.NOT_FOUND]:
                self.log.info(
                    "pod_delete_stopping_first",
                    resource=self.config.resource_name,
                    instance_id=self.instance_id,
                    current_state=current_state.value,
                    trace_id=self.trace_id
                )

            tmp_path = self._render_all_yamls()
            try:
                self._run_kubectl(["delete", "-f", str(tmp_path), "-n", self.namespace, "--ignore-not-found=true"], check=False)
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()

            if remove_pvcs:
                self.log.info(
                    "pod_delete_removing_pvcs",
                    resource=self.config.resource_name,
                    instance_id=self.instance_id,
                    trace_id=self.trace_id
                )
                self._run_kubectl([
                    "delete", "pvc",
                    "-n", self.namespace,
                    "-l", f"instance={self.instance_id}",
                    "--ignore-not-found=true"
                ], check=False)

            duration = int((time.time() - start_time) * 1000)
            final_state = self.get_status()
            success = final_state == PodState.NOT_FOUND

            self.log.info(
                "pod_delete_complete",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
                initial_state=current_state.value,
                final_state=final_state.value,
                pvcs_removed=remove_pvcs,
                success=success,
                duration_ms=duration,
                trace_id=self.trace_id
            )
            return success

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.exception(
                "pod_delete_failed",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
                duration_ms=duration,
                error=e,
                trace_id=self.trace_id
            )
            return False

    def scale(self, replicas: int) -> bool:
        start_time = time.time()

        self.log.info(
            "deployment_scale_requested",
            resource=self.config.resource_name,
            instance_id=self.instance_id,
            namespace=self.namespace,
            replicas=replicas,
            trace_id=self.trace_id
        )

        try:
            self._run_kubectl([
                "scale", "deployment",
                "-n", self.namespace,
                "-l", f"instance={self.instance_id}",
                f"--replicas={replicas}"
            ])

            duration = int((time.time() - start_time) * 1000)

            self.log.info(
                "deployment_scale_complete",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
                replicas=replicas,
                duration_ms=duration,
                trace_id=self.trace_id
            )

            return True

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.exception(
                "deployment_scale_failed",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
                replicas=replicas,
                duration_ms=duration,
                error=e,
                trace_id=self.trace_id
            )
            return False

    def create_hpa(self, min_replicas: int = 1, max_replicas: int = 10, cpu_percent: int = 80, memory_percent: Optional[int] = None) -> bool:
        start_time = time.time()

        self.log.info(
            "hpa_create_requested",
            resource=self.config.resource_name,
            instance_id=self.instance_id,
            namespace=self.namespace,
            min_replicas=min_replicas,
            max_replicas=max_replicas,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            trace_id=self.trace_id
        )

        try:
            cmd = [
                "autoscale", "deployment",
                "-n", self.namespace,
                "-l", f"instance={self.instance_id}",
                f"--min={min_replicas}",
                f"--max={max_replicas}",
                f"--cpu-percent={cpu_percent}"
            ]

            self._run_kubectl(cmd)

            duration = int((time.time() - start_time) * 1000)

            self.log.info(
                "hpa_create_complete",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
                min_replicas=min_replicas,
                max_replicas=max_replicas,
                duration_ms=duration,
                trace_id=self.trace_id
            )

            return True

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.exception(
                "hpa_create_failed",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
                duration_ms=duration,
                error=e,
                trace_id=self.trace_id
            )
            return False

    def delete_hpa(self) -> bool:
        start_time = time.time()

        self.log.info(
            "hpa_delete_requested",
            resource=self.config.resource_name,
            instance_id=self.instance_id,
            namespace=self.namespace,
            trace_id=self.trace_id
        )

        try:
            self._run_kubectl([
                "delete", "hpa",
                "-n", self.namespace,
                "-l", f"instance={self.instance_id}",
                "--ignore-not-found=true"
            ], check=False)

            duration = int((time.time() - start_time) * 1000)

            self.log.info(
                "hpa_delete_complete",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
                duration_ms=duration,
                trace_id=self.trace_id
            )

            return True

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.log.exception(
                "hpa_delete_failed",
                resource=self.config.resource_name,
                instance_id=self.instance_id,
                namespace=self.namespace,
                duration_ms=duration,
                error=e,
                trace_id=self.trace_id
            )
            return False
