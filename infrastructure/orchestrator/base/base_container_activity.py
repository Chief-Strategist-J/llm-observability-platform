from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
import logging
import time
import concurrent.futures
import re

import docker
from docker import DockerClient
from docker.models.containers import Container
from docker.errors import NotFound, ImageNotFound, DockerException, APIError

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
)
logger = logging.getLogger(__name__)


class ContainerState(Enum):
    RUNNING = "running"
    STARTING = "created"
    STOPPED = "exited"
    PAUSED = "paused"
    RESTARTING = "restarting"
    DEAD = "dead"
    UNKNOWN = "unknown"


@dataclass
class ContainerConfig:
    image: str
    name: str
    ports: Dict[int, int] = field(default_factory=dict)
    volumes: Dict[
        str, Union[str, Tuple[str, str], List[Any], Dict[str, Any]]
    ] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    command: Optional[Union[str, List[str]]] = None
    entrypoint: Optional[Union[str, List[str]]] = None
    working_dir: Optional[str] = None
    user: Optional[str] = None
    network: Optional[str] = "bridge"
    hostname: Optional[str] = None
    domainname: Optional[str] = None
    dns: List[str] = field(default_factory=list)
    dns_search: List[str] = field(default_factory=list)
    extra_hosts: Dict[str, str] = field(default_factory=dict)
    memory: Optional[str] = "512m"
    memory_swap: Optional[str] = None
    memory_reservation: Optional[str] = "256m"
    cpus: Optional[float] = 1.0
    cpu_shares: Optional[int] = 1024
    cpu_quota: Optional[int] = None
    cpu_period: Optional[int] = None
    cpuset_cpus: Optional[str] = None
    replicas: int = 1
    restart: str = "unless-stopped"
    detach: bool = True
    stdin_open: bool = False
    tty: bool = False
    remove: bool = False
    privileged: bool = False
    read_only: bool = False
    cap_add: List[str] = field(default_factory=list)
    cap_drop: List[str] = field(default_factory=list)
    devices: List[str] = field(default_factory=list)
    device_requests: List[Dict[str, Any]] = field(default_factory=list)
    healthcheck: Optional[Dict[str, Any]] = None
    log_driver: Optional[str] = None
    log_options: Dict[str, str] = field(default_factory=dict)
    shm_size: Optional[str] = None
    tmpfs: Dict[str, str] = field(default_factory=dict)
    ulimits: List[Dict[str, Any]] = field(default_factory=list)
    sysctls: Dict[str, str] = field(default_factory=dict)
    security_opt: List[str] = field(default_factory=list)
    storage_opt: Dict[str, str] = field(default_factory=dict)
    timeout: int = 60
    pull_timeout: int = 300
    retry_attempts: int = 3
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        logger.debug("Validating ContainerConfig for %s", self.name)
        if not self.image or not self.name:
            raise ValueError("image and name are required")
        if self.replicas < 1:
            raise ValueError("replicas must be >= 1")


class BaseContainerManager(ABC):
    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self, timeout: int = 10) -> None:
        raise NotImplementedError

    @abstractmethod
    def restart(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, force: bool = False) -> None:
        raise NotImplementedError

    @abstractmethod
    def logs(self, follow: bool = False) -> str:
        raise NotImplementedError



def _normalize_volumes_for_docker(
    volumes: Dict[str, Union[str, Tuple[str, str], List[Any], Dict[str, Any]]]
) -> Dict[str, Dict[str, str]]:

    normalized: Dict[str, Dict[str, str]] = {}
    for host, val in volumes.items():
        if val is None:
            continue
        if isinstance(val, str):
            normalized[host] = {"bind": val, "mode": "rw"}
            continue
        if isinstance(val, (list, tuple)):
            if len(val) == 0:
                raise TypeError(f"Invalid empty list/tuple for volume {host}")
            bind = val[0]
            mode = val[1] if len(val) > 1 else "rw"
            if not isinstance(bind, str):
                raise TypeError(f"Invalid bind path for {host}: {bind!r}")
            normalized[host] = {"bind": bind, "mode": str(mode)}
            continue
        if isinstance(val, dict):
            if "bind" in val:
                bind = val["bind"]
                mode = val.get("mode", "rw")
                if not isinstance(bind, str):
                    raise TypeError(f"Invalid bind path for {host}: {bind!r}")
                normalized[host] = {"bind": bind, "mode": str(mode)}
                continue
            raise TypeError(f"Unsupported dict shape for volume {host}: {val!r}")
        raise TypeError(f"Unsupported volume value type for {host}: {type(val).__name__}")
    return normalized


def _validate_and_normalize_volumes_in_run_args(run_args: Dict[str, Any]) -> None:
    if "volumes" not in run_args:
        return

    raw = run_args["volumes"]
    if not isinstance(raw, dict):
        raise TypeError(f"'volumes' run-arg must be a dict; got {type(raw).__name__}")

    
    if all(isinstance(v, dict) and "bind" in v for v in raw.values()):
        return

    normalized = _normalize_volumes_for_docker(raw)
    run_args["volumes"] = normalized



class ContainerManager(BaseContainerManager):
    def __init__(self, config: ContainerConfig) -> None:
        self.config = config
        self.config.validate()
        self.client: DockerClient = DockerClient.from_env()
        self.container: Optional[Container] = None

    
    def _ensure_image_exists(self) -> None:
        try:
            logger.debug("Checking image locally: %s", self.config.image)
            self.client.images.get(self.config.image)
            logger.debug("Image %s exists locally", self.config.image)
        except ImageNotFound:
            logger.info("Image %s not found locally — pulling", self.config.image)
            self._pull_image()
        except DockerException as e:
            logger.exception("Error while inspecting image %s: %s", self.config.image, e)
            raise

    def _pull_image(self) -> None:
        attempts = max(1, int(self.config.retry_attempts))
        last_exc: Optional[Exception] = None
        for attempt in range(1, attempts + 1):
            try:
                logger.info("Pulling image %s (attempt %d/%d)", self.config.image, attempt, attempts)
                if self.config.pull_timeout and self.config.pull_timeout > 0:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                        future = ex.submit(self.client.images.pull, self.config.image)
                        try:
                            future.result(timeout=self.config.pull_timeout)
                        except concurrent.futures.TimeoutError as te:
                            raise TimeoutError(f"Image pull timed out after {self.config.pull_timeout}s") from te
                else:
                    self.client.images.pull(self.config.image)
                logger.info("Successfully pulled image %s", self.config.image)
                return
            except Exception as exc:
                last_exc = exc
                logger.warning("Pull attempt %d failed for %s: %s", attempt, self.config.image, exc)
                time.sleep(2 * attempt)
        logger.error("Failed to pull image %s after %d attempts", self.config.image, attempts)
        if last_exc:
            raise last_exc
        raise RuntimeError("Unknown error pulling image")

    
    def _is_builtin_network(self, network_name: Optional[str]) -> bool:
        
        return not network_name or network_name == "bridge"

    def _ensure_network_exists(self) -> None:
        net_name = self.config.network
        if self._is_builtin_network(net_name):
            logger.debug("Network is builtin or unspecified (%r) — skipping create", net_name)
            return

        assert net_name is not None
        try:
            logger.debug("Checking Docker network exists: %s", net_name)
            self.client.networks.get(net_name)
            logger.debug("Docker network %s exists", net_name)
        except NotFound:
            try:
                logger.info("Creating Docker network: %s", net_name)
                self.client.networks.create(net_name, driver="bridge")
                logger.info("Docker network %s created", net_name)
            except APIError as api_err:
                logger.exception("Failed to create Docker network %s: %s", net_name, api_err)
                raise
        except DockerException as e:
            logger.exception("Error while checking/creating Docker network %s: %s", net_name, e)
            raise

    def start(self) -> None:
        logger.debug("Starting container: %s", self.config.name)
        try:
            existing = self._get_existing_container()
            try:
                self._ensure_network_exists()
            except Exception:
                logger.warning("Network ensure step failed; continuing to attempt start/create (may still error)")

            if existing:
                logger.info("Container %s already exists; starting.", self.config.name)
                try:
                    existing.start()
                    self.container = existing
                    return
                except DockerException as start_exc:
                    msg = str(start_exc).lower()
                    if "network" in msg and "not found" in msg:
                        logger.warning("Start failed due to missing network; attempting to (re)create network and retry start")
                        self._ensure_network_exists()
                        existing.start()
                        self.container = existing
                        return
                    logger.exception("Failed to start existing container %s: %s", self.config.name, start_exc)
                    raise

            self._ensure_image_exists()

            run_args: Dict[str, Any] = {
                "image": self.config.image,
                "name": self.config.name,
                "detach": self.config.detach,
                "restart_policy": {"Name": self.config.restart},
            }

            def add_arg(key: str, value: Any) -> None:
                if value not in (None, {}, [], ""):
                    run_args[key] = value

            add_arg("ports", self.config.ports)
            if self.config.volumes:
                add_arg("volumes", _normalize_volumes_for_docker(self.config.volumes))
            add_arg("environment", self.config.environment)
            add_arg("labels", self.config.labels)
            add_arg("command", self.config.command)
            add_arg("entrypoint", self.config.entrypoint)
            add_arg("working_dir", self.config.working_dir)
            add_arg("user", self.config.user)
            add_arg("network", self.config.network)
            add_arg("hostname", self.config.hostname)
            add_arg("domainname", self.config.domainname)
            add_arg("dns", self.config.dns)
            add_arg("dns_search", self.config.dns_search)
            add_arg("extra_hosts", self.config.extra_hosts)

            add_arg("mem_limit", self.config.memory)
            add_arg("memswap_limit", self.config.memory_swap)
            add_arg("mem_reservation", self.config.memory_reservation)

            # CPU mapping
            if self.config.cpus not in (None, ""):
                try:
                    cpus_val = float(self.config.cpus)
                    if cpus_val > 0:
                        run_args["nano_cpus"] = int(cpus_val * 1_000_000_000)
                        logger.debug("Mapped cpus=%s -> nano_cpus=%d", cpus_val, run_args["nano_cpus"])
                except (TypeError, ValueError) as exc:
                    logger.warning("Invalid cpus value %r: %s (skipping)", self.config.cpus, exc)

            add_arg("cpu_shares", self.config.cpu_shares)
            add_arg("cpu_quota", self.config.cpu_quota)
            add_arg("cpu_period", self.config.cpu_period)
            add_arg("cpuset_cpus", self.config.cpuset_cpus)

            add_arg("stdin_open", self.config.stdin_open)
            add_arg("tty", self.config.tty)
            add_arg("remove", self.config.remove)
            add_arg("privileged", self.config.privileged)
            add_arg("read_only", self.config.read_only)
            add_arg("cap_add", self.config.cap_add)
            add_arg("cap_drop", self.config.cap_drop)
            add_arg("devices", self.config.devices)
            add_arg("device_requests", self.config.device_requests)
            add_arg("healthcheck", self.config.healthcheck)
            add_arg("log_driver", self.config.log_driver)
            add_arg("log_opts", self.config.log_options)
            add_arg("shm_size", self.config.shm_size)
            add_arg("tmpfs", self.config.tmpfs)
            add_arg("ulimits", self.config.ulimits)
            add_arg("sysctls", self.config.sysctls)
            add_arg("security_opt", self.config.security_opt)
            add_arg("storage_opt", self.config.storage_opt)

            if self.config.extra_params:
                run_args.update(self.config.extra_params)

            _validate_and_normalize_volumes_in_run_args(run_args)

            debug_args = {k: v for k, v in run_args.items() if k not in ("environment", "labels", "volumes")}
            logger.debug("Calling containers.run with args (sample): %s", debug_args)

            try:
                self.container = self.client.containers.run(**run_args)
                logger.info("Container %s created & started.", self.config.name)
            except DockerException as run_exc:
                msg = str(run_exc).lower()
                if "network" in msg and "not found" in msg:
                    logger.warning("containers.run failed due to missing network; attempting to create network and retry")
                    self._ensure_network_exists()
                    try:
                        self.container = self.client.containers.get(self.config.name)
                        self.container.start()
                        logger.info("Container %s started after creating network.", self.config.name)
                        return
                    except Exception as second_exc:
                        logger.exception("Retry after network create failed: %s", second_exc)
                        raise
                logger.exception("containers.run raised an error: %s", run_exc)
                raise

        except DockerException as de:
            logger.exception("DockerException when starting container %s: %s", self.config.name, de)
            raise
        except Exception:
            logger.exception("Unexpected error when starting container %s", self.config.name)
            raise

    def stop(self, timeout: int = 10) -> None:
        logger.debug("Stopping container: %s", self.config.name)
        container = self._get_existing_container()
        if container:
            container.stop(timeout=timeout)
            logger.info("Container %s stopped.", self.config.name)
        else:
            logger.warning("Container %s not present (stop skipped).", self.config.name)

    def restart(self) -> None:
        logger.debug("Restarting container: %s", self.config.name)
        container = self._get_existing_container()
        if container:
            container.restart()
            logger.info("Container %s restarted.", self.config.name)
        else:
            logger.warning("Container %s not present (restart skipped).", self.config.name)

    def delete(self, force: bool = False, backup: bool = True) -> None:
        import threading
        import datetime
        import os
        from pathlib import Path
        from docker.errors import ImageNotFound, NotFound

        if not hasattr(self, "_delete_lock"):
            self._delete_lock = threading.RLock()

        with self._delete_lock:
            container = self._get_existing_container()
            if not container:
                logger.warning("Container %s not present (delete skipped).",
                            self.config.name)
                return

            errors: list[str] = []
            ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            backup_dir = Path(os.getcwd()) / "container_backups"
            backup_dir.mkdir(parents=True, exist_ok=True)

            try:
                try:
                    container.reload()
                except Exception:
                    pass

                if backup:
                    try:
                        if getattr(container, "status", "") == "running":
                            try:
                                container.stop(timeout=30)
                            except Exception as e:
                                if force:
                                    try:
                                        container.kill()
                                    except Exception:
                                        pass
                                else:
                                    raise
                        export_name = backup_dir / f"{self.config.name}_export_{ts}.tar"
                        with export_name.open("wb") as f:
                            for chunk in container.export():
                                f.write(chunk)
                        logger.info("Wrote container export %s", export_name)
                    except Exception as e:
                        logger.exception("Container export failed: %s", e)
                        raise

                    try:
                        image_repo = f"{self.config.name}_backup"
                        image_tag = ts
                        img_id = None
                        image_obj = None
                        if hasattr(container, "commit"):
                            image_obj = container.commit(repository=image_repo,
                                                        tag=image_tag)
                            img_id = getattr(image_obj, "id", None)
                        else:
                            commit_res = self.client.api.commit(
                                container=container.id,
                                repository=image_repo,
                                tag=image_tag,
                            )
                            if isinstance(commit_res, dict):
                                img_id = commit_res.get("Id") or commit_res.get("id")
                            elif isinstance(commit_res, str):
                                img_id = commit_res

                        if not image_obj:
                            if not img_id:
                                raise RuntimeError("Could not determine committed image id")
                            image_obj = self.client.images.get(img_id)

                        save_name = backup_dir / f"{self.config.name}_image_{ts}.tar"
                        with save_name.open("wb") as f:
                            for chunk in image_obj.save(named=True):
                                f.write(chunk)
                        logger.info("Wrote image backup %s", save_name)
                    except Exception as e:
                        logger.exception("Image commit/save failed: %s", e)
                        raise

                try:
                    try:
                        container.reload()
                    except Exception:
                        pass

                    if getattr(container, "status", "") == "running":
                        try:
                            container.stop(timeout=30)
                            logger.info("Container %s stopped.", self.config.name)
                        except Exception as e:
                            if force:
                                try:
                                    container.kill()
                                except Exception as e2:
                                    errors.append(f"kill: {e2}")
                            else:
                                errors.append(f"stop: {e}")

                    try:
                        container.remove(force=force)
                        logger.info("Container %s removed.", self.config.name)
                    except Exception as e:
                        errors.append(f"container remove: {e}")
                except Exception as e:
                    errors.append(f"container ops: {e}")

                try:
                    self.client.images.remove(self.config.image, force=force)
                    logger.info("Image %s removed.", self.config.image)
                except ImageNotFound:
                    logger.debug("Image %s not found.", self.config.image)
                except Exception as e:
                    errors.append(f"image remove: {e}")

                for vol_name in list(self.config.volumes.keys()):
                    if not vol_name or "/" in vol_name or ":" in vol_name:
                        continue
                    try:
                        vol = self.client.volumes.get(vol_name)
                        vol.remove(force=force)
                        logger.info("Volume %s removed.", vol_name)
                    except NotFound:
                        logger.debug("Volume %s not found.", vol_name)
                    except Exception as e:
                        errors.append(f"volume {vol_name}: {e}")

                net_name = getattr(self.config, "network", None)
                if net_name and net_name not in ("bridge", "host", "none"):
                    try:
                        net = self.client.networks.get(net_name)
                        net.remove()
                        logger.info("Network %s removed.", net_name)
                    except NotFound:
                        logger.debug("Network %s not found.", net_name)
                    except Exception as e:
                        errors.append(f"network {net_name}: {e}")

                if errors:
                    msg = "Delete completed with errors: " + "; ".join(errors)
                    logger.error(msg)
                    raise Exception(msg)
            except Exception:
                raise

    def logs(self, follow: bool = False) -> str:
        logger.debug("Fetching logs for container: %s", self.config.name)
        container = self._get_existing_container()
        if not container:
            logger.warning("Container %s not present (logs empty).", self.config.name)
            return ""
        logs_bytes = container.logs(follow=follow)
        return logs_bytes.decode("utf-8", errors="ignore")

    def _get_existing_container(self) -> Optional[Container]:
        try:
            return self.client.containers.get(self.config.name)
        except NotFound:
            return None


class BaseService:
    def __init__(self, config: ContainerConfig, extra: Optional[Dict[str, str]] = None) -> None:
        self.config = config
        self.extra = extra or {}
        self.manager = ContainerManager(self.config)

    def run(self) -> None:
        self.manager.start()

    def stop(self, timeout: int = 10) -> None:
        self.manager.stop(timeout=timeout)

    def restart(self) -> None:
        self.manager.restart()

    def delete(self, force: bool = False) -> None:
        self.manager.delete(force=force)

    def exec(self, cmd: str) -> Tuple[int, str]:
        container = self.manager._get_existing_container()
        if not container:
            raise RuntimeError("Container not running")
        exec_res = container.exec_run(cmd, demux=True)
        exit_code = getattr(exec_res, "exit_code", 0)
        out = getattr(exec_res, "output", None)
        output_bytes = b""
        if isinstance(out, tuple):
            stdout, stderr = out
            if stdout:
                output_bytes += stdout
            if stderr:
                output_bytes += stderr
        elif isinstance(out, (bytes, bytearray)):
            output_bytes = out
        else:
            output_bytes = str(out).encode("utf-8", errors="ignore")
        return int(exit_code), output_bytes.decode("utf-8", errors="ignore")
