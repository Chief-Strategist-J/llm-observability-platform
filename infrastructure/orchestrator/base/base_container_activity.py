from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Tuple, TYPE_CHECKING
from enum import Enum
import logging
import time
import concurrent.futures
import re

# Avoid importing docker at module import time so this module can be safely imported
# inside contexts that require deterministic imports (e.g., Temporal workflow sandbox).
# Docker is imported lazily inside functions/constructors at runtime.

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
)
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    # For type-checking only; these imports will not execute at runtime.
    from docker import DockerClient  # type: ignore
    from docker.models.containers import Container  # type: ignore


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
        self,
        volumes: Dict[str, Union[str, Tuple[str, str], List[Any], Dict[str, Any]]]
    ) -> Dict[str, Dict[str, str]]:

        logger.debug("volume_normalize_start volumes_count=%s", len(volumes))
        normalized: Dict[str, Dict[str, str]] = {}

        try:
            for host, val in volumes.items():
                logger.debug("volume_normalize_item host=%s type=%s", host, type(val).__name__)

                if val is None:
                    logger.debug("volume_normalize_skip_none host=%s", host)
                    continue

                if isinstance(val, str):
                    normalized[host] = {"bind": val, "mode": "rw"}
                    logger.debug("volume_normalize_simple host=%s bind=%s", host, val)
                    continue

                if isinstance(val, (list, tuple)):
                    if len(val) == 0:
                        raise TypeError(f"Invalid empty list/tuple for volume {host}")

                    bind = val[0]
                    mode = val[1] if len(val) > 1 else "rw"

                    if not isinstance(bind, str):
                        raise TypeError(f"Invalid bind path for {host}: {bind!r}")

                    normalized[host] = {"bind": bind, "mode": str(mode)}
                    logger.debug("volume_normalize_sequence host=%s bind=%s mode=%s", host, bind, mode)
                    continue

                if isinstance(val, dict):
                    if "bind" in val:
                        bind = val["bind"]
                        mode = val.get("mode", "rw")

                        if not isinstance(bind, str):
                            raise TypeError(f"Invalid bind path for {host}: {bind!r}")

                        normalized[host] = {"bind": bind, "mode": str(mode)}
                        logger.debug("volume_normalize_dict host=%s bind=%s mode=%s", host, bind, mode)
                        continue

                    raise TypeError(f"Unsupported dict shape for volume {host}: {val!r}")

                raise TypeError(f"Unsupported volume value type for {host}: {type(val).__name__}")

        except Exception as e:
            logger.exception("volume_normalize_error error=%s", e)
            raise

        logger.debug("volume_normalize_complete normalized_count=%s", len(normalized))
        return normalized


    def _validate_and_normalize_volumes_in_run_args(self, run_args: Dict[str, Any]) -> None:
        logger.debug("volume_runargs_validate_start run_args_keys=%s", list(run_args.keys()))

        try:
            if "volumes" not in run_args:
                logger.debug("volume_runargs_no_volumes")
                return

            raw = run_args["volumes"]
            logger.debug("volume_runargs_raw_type type=%s", type(raw).__name__)

            if not isinstance(raw, dict):
                raise TypeError(f"'volumes' run-arg must be a dict; got {type(raw).__name__}")

            if all(isinstance(v, dict) and "bind" in v for v in raw.values()):
                logger.debug("volume_runargs_already_normalized")
                return

            logger.debug("volume_runargs_normalizing")
            normalized = self._normalize_volumes_for_docker(raw)
            run_args["volumes"] = normalized
            logger.debug("volume_runargs_normalized volume_count=%s", len(normalized))

        except Exception as e:
            logger.exception("volume_runargs_validate_error error=%s", e)
            raise

        logger.debug("volume_runargs_validate_complete")


    def get_docker_client(self):
        logger.debug("docker_client_init_start")

        try:
            import docker
            client = docker.from_env()

            logger.debug("docker_client_init_success")
            return client

        except Exception as e:
            logger.exception("docker_client_init_error error=%s", e)
            raise



class ContainerManager(BaseContainerManager):
    def __init__(self, config: ContainerConfig) -> None:
        self.config = config
        self.config.validate()

        self.client = self.get_docker_client()
        self.container: Optional["Container"] = None

    def _ensure_image_exists(self) -> None:
        from docker.errors import ImageNotFound, DockerException  # type: ignore

        logger.debug("image_check_start name=%s image=%s", self.config.name, self.config.image)
        try:
            self.client.images.get(self.config.image)
            logger.debug("image_check_exists name=%s image=%s", self.config.name, self.config.image)
        except ImageNotFound:
            logger.debug("image_check_missing name=%s image=%s", self.config.name, self.config.image)
            try:
                self._pull_image()
            except Exception as e:
                logger.exception("image_check_pull_error name=%s image=%s error=%s", self.config.name, self.config.image, e)
                raise
        except DockerException as e:
            logger.exception("image_check_error name=%s image=%s error=%s", self.config.name, self.config.image, e)
            raise
        logger.debug("image_check_complete name=%s image=%s", self.config.name, self.config.image)


    def _pull_image(self) -> None:
        attempts = max(1, int(self.config.retry_attempts))
        logger.debug("image_pull_start name=%s image=%s attempts=%s", self.config.name, self.config.image, attempts)

        last_exc: Optional[Exception] = None
        for attempt in range(1, attempts + 1):
            logger.debug("image_pull_attempt_start name=%s image=%s attempt=%s", self.config.name, self.config.image, attempt)
            try:
                if self.config.pull_timeout and self.config.pull_timeout > 0:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                        future = ex.submit(self.client.images.pull, self.config.image)
                        try:
                            future.result(timeout=self.config.pull_timeout)
                        except concurrent.futures.TimeoutError as te:
                            logger.debug("image_pull_timeout name=%s image=%s timeout=%s attempt=%s",
                                         self.config.name, self.config.image, self.config.pull_timeout, attempt)
                            raise TimeoutError(f"Image pull timed out after {self.config.pull_timeout}s") from te
                else:
                    self.client.images.pull(self.config.image)

                logger.info("Successfully pulled image %s", self.config.image)
                logger.debug("image_pull_attempt_success name=%s image=%s attempt=%s",
                             self.config.name, self.config.image, attempt)
                return

            except Exception as exc:
                last_exc = exc
                logger.debug("image_pull_attempt_error name=%s image=%s attempt=%s error=%s",
                             self.config.name, self.config.image, attempt, exc)
                time.sleep(2 * attempt)

        logger.error("Failed to pull image %s after %d attempts", self.config.image, attempts)
        logger.debug("image_pull_failed name=%s image=%s attempts=%s", self.config.name, self.config.image, attempts)

        if last_exc:
            raise last_exc
        raise RuntimeError("Unknown error pulling image")


    def _is_builtin_network(self, network_name: Optional[str]) -> bool:
        logger.debug("network_builtin_check name=%s network=%s", self.config.name, network_name)
        result = not network_name or network_name == "bridge"
        logger.debug("network_builtin_result name=%s network=%s result=%s", self.config.name, network_name, result)
        return result

    def _ensure_network_exists(self) -> None:
        from docker.errors import NotFound, DockerException
        net_name = self.config.network
        if not net_name or net_name in ("bridge",):
            logger.debug("Using builtin network: %s", net_name)
            return
        try:
            logger.debug("Checking network: %s", net_name)
            self.client.networks.get(net_name)
            logger.info("Network %s already exists", net_name)
        except NotFound:
            try:
                logger.info("Creating network: %s", net_name)
                self.client.networks.create(net_name, driver="bridge")
                logger.info("Network %s created", net_name)
            except Exception as e:
                logger.exception("Network creation failed: %s", e)
                raise
        except DockerException as e:
            logger.exception("Network lookup failed: %s", e)
            raise
   
    def _ensure_container_on_network(self, container):
        try:
            net_name = self.config.network
            if not net_name or net_name in ("bridge", "host", "none"):
                logger.debug("No external network required for %s", self.config.name)
                return
            net = self.client.networks.get(net_name)
            container.reload()
            networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})
            if net_name in networks:
                logger.debug("Container %s already attached to %s", self.config.name, net_name)
                return
            logger.info("Attaching container %s to network %s", self.config.name, net_name)
            net.connect(container)
            logger.info("Container %s attached to network %s", self.config.name, net_name)
        except Exception as e:
            logger.exception("Network attach failed for %s: %s", self.config.name, e)


    def start(self) -> None:
        from docker.errors import DockerException, NotFound
        logger.debug("Starting container: %s", self.config.name)
        try:
            existing = self._get_existing_container()
            try:
                self._ensure_network_exists()
            except Exception:
                logger.warning("Network ensure step failed; continuing start")

            if existing:
                logger.info("Container %s already exists; starting.", self.config.name)
                try:
                    existing.start()
                    self._ensure_container_on_network(existing)
                    self.container = existing
                    return
                except DockerException as start_exc:
                    msg = str(start_exc).lower()
                    if "network" in msg and "not found" in msg:
                        logger.warning("Start failed due to missing network; recreating")
                        self._ensure_network_exists()
                        existing.start()
                        self._ensure_container_on_network(existing)
                        self.container = existing
                        return
                    logger.exception("Failed to start existing container %s: %s", self.config.name, start_exc)
                    raise

            self._ensure_image_exists()

            run_args = {
                "image": self.config.image,
                "name": self.config.name,
                "detach": self.config.detach,
                "restart_policy": {"Name": self.config.restart},
            }

            def add_arg(k, v):
                if v not in (None, {}, [], ""):
                    run_args[k] = v

            add_arg("ports", self.config.ports)
            if self.config.volumes:
                add_arg("volumes", self._normalize_volumes_for_docker(self.config.volumes))
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

            if self.config.cpus not in (None, ""):
                try:
                    cv = float(self.config.cpus)
                    if cv > 0:
                        run_args["nano_cpus"] = int(cv * 1_000_000_000)
                        logger.debug("Mapped cpus=%s -> nano_cpus=%d", cv, run_args["nano_cpus"])
                except Exception as exc:
                    logger.warning("Invalid cpus value %r: %s", self.config.cpus, exc)

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

            self._validate_and_normalize_volumes_in_run_args(run_args)

            debug_args = {k: v for k, v in run_args.items() if k not in ("environment", "labels", "volumes")}
            logger.debug("Calling containers.run args: %s", debug_args)

            try:
                self.container = self.client.containers.run(**run_args)
                self._ensure_container_on_network(self.container)
                logger.info("Container %s created & started.", self.config.name)
            except DockerException as run_exc:
                msg = str(run_exc).lower()
                if "network" in msg and "not found" in msg:
                    logger.warning("Run failed due to network missing; recreating network")
                    self._ensure_network_exists()
                    try:
                        self.container = self.client.containers.get(self.config.name)
                        self.container.start()
                        self._ensure_container_on_network(self.container)
                        logger.info("Container %s started after recreate.", self.config.name)
                        return
                    except Exception as second_exc:
                        logger.exception("Retry after network create failed: %s", second_exc)
                        raise
                logger.exception("containers.run failed: %s", run_exc)
                raise

        except Exception as de:
            logger.exception("Error when starting container %s: %s", self.config.name, de)
            raise

    def stop(self, timeout: int = 10) -> None:
        logger.debug("container_stop_start name=%s timeout=%s", self.config.name, timeout)
        try:
            container = self._get_existing_container()
            if container:
                try:
                    container.stop(timeout=timeout)
                    logger.info("Container %s stopped.", self.config.name)
                except Exception as e:
                    logger.exception("container_stop_error name=%s timeout=%s error=%s", self.config.name, timeout, e)
                    raise
            else:
                logger.debug("container_stop_notfound name=%s", self.config.name)
        except Exception as e:
            logger.exception("container_stop_wrapper_error name=%s error=%s", self.config.name, e)
            raise
        logger.debug("container_stop_complete name=%s timeout=%s", self.config.name, timeout)


    def restart(self) -> None:
        logger.debug("container_restart_start name=%s", self.config.name)
        try:
            container = self._get_existing_container()
            if container:
                try:
                    container.restart()
                    logger.info("Container %s restarted.", self.config.name)
                except Exception as e:
                    logger.exception("container_restart_error name=%s error=%s", self.config.name, e)
                    raise
            else:
                logger.debug("container_restart_notfound name=%s", self.config.name)
        except Exception as e:
            logger.exception("container_restart_wrapper_error name=%s error=%s", self.config.name, e)
            raise
        logger.debug("container_restart_complete name=%s", self.config.name)

    def logs(self, follow: bool = False) -> str:
        logger.debug("container_logs_fetch_start name=%s follow=%s", self.config.name, follow)
        try:
            container = self._get_existing_container()
            if not container:
                logger.debug("container_logs_not_found name=%s", self.config.name)
                return ""

            logs_bytes = container.logs(follow=follow)
            logger.debug(
                "container_logs_fetch_complete name=%s type=%s",
                self.config.name,
                type(logs_bytes),
            )

            if isinstance(logs_bytes, (bytes, bytearray)):
                return logs_bytes.decode("utf-8", errors="ignore")

            return str(logs_bytes)

        except Exception as e:
            logger.exception("container_logs_error name=%s error=%s", self.config.name, e)
            raise


    def _get_existing_container(self) -> Optional["Container"]:
        from docker.errors import NotFound  # type: ignore
        logger.debug("container_lookup_start name=%s", self.config.name)
        try:
            container = self.client.containers.get(self.config.name)
            logger.debug("container_lookup_found name=%s", self.config.name)
            return container
        except NotFound:
            logger.debug("container_lookup_notfound name=%s", self.config.name)
            return None
        except Exception as e:
            logger.exception("container_lookup_error name=%s error=%s", self.config.name, e)
            raise
        
    def delete(self, force: bool = False, backup: bool = False) -> None:
        logger.debug(
            "container_delete_start name=%s force=%s backup=%s",
            self.config.name,
            force,
            backup,
        )

        import threading
        import datetime
        import os
        from pathlib import Path
        from docker.errors import ImageNotFound, NotFound

        try:
            if not hasattr(self, "_delete_lock"):
                self._delete_lock = threading.RLock()

            with self._delete_lock:
                logger.debug(
                    "container_delete_lock_acquired name=%s",
                    self.config.name,
                )

                container = self._get_existing_container()
                if not container:
                    logger.debug(
                        "container_delete_container_missing name=%s",
                        self.config.name,
                    )
                    return

                errors: list[str] = []
                ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                backup_dir = Path(os.getcwd()) / "container_backups"
                backup_dir.mkdir(parents=True, exist_ok=True)

                logger.debug(
                    "container_delete_initialized name=%s timestamp=%s backup_dir=%s",
                    self.config.name,
                    ts,
                    backup_dir,
                )

                try:
                    try:
                        container.reload()
                        logger.debug("container_delete_reload_ok name=%s", self.config.name)
                    except Exception:
                        logger.debug("container_delete_reload_failed name=%s", self.config.name)

                    if backup:
                        logger.debug("container_delete_backup_start name=%s", self.config.name)
                        try:
                            if getattr(container, "status", "") == "running":
                                try:
                                    container.stop(timeout=30)
                                    logger.debug("container_delete_backup_stopped name=%s", self.config.name)
                                except Exception as e:
                                    if force:
                                        try:
                                            container.kill()
                                            logger.debug("container_delete_backup_killed name=%s", self.config.name)
                                        except Exception:
                                            logger.debug("container_delete_backup_kill_failed name=%s", self.config.name)
                                    else:
                                        raise
                            export_name = backup_dir / f"{self.config.name}_export_{ts}.tar"
                            with export_name.open("wb") as f:
                                for chunk in container.export():
                                    f.write(chunk)
                            logger.info("Wrote container export %s", export_name)
                        except Exception as e:
                            logger.exception(
                                "container_delete_backup_export_failed name=%s error=%s",
                                self.config.name,
                                e,
                            )
                            raise

                        try:
                            image_repo = f"{self.config.name}_backup"
                            image_tag = ts
                            img_id = None
                            image_obj = None
                            if hasattr(container, "commit"):
                                image_obj = container.commit(
                                    repository=image_repo,
                                    tag=image_tag
                                )
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
                            logger.exception(
                                "container_delete_backup_image_failed name=%s error=%s",
                                self.config.name,
                                e,
                            )
                            raise

                except Exception as e:
                    logger.debug(
                        "container_delete_backup_ops_error name=%s error=%s",
                        self.config.name,
                        e,
                    )
                    raise

                try:
                    try:
                        container.reload()
                        logger.debug("container_delete_reload2_ok name=%s", self.config.name)
                    except Exception:
                        logger.debug("container_delete_reload2_failed name=%s", self.config.name)

                    if getattr(container, "status", "") == "running":
                        try:
                            container.stop(timeout=30)
                            logger.info("Container %s stopped.", self.config.name)
                        except Exception as e:
                            if force:
                                try:
                                    container.kill()
                                    logger.debug("container_delete_killed name=%s", self.config.name)
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
                        containers_attached = net.attrs.get("Containers") or {}
                        if containers_attached:
                            try:
                                target_id = getattr(container, "id", None)
                                if target_id and target_id in containers_attached:
                                    try:
                                        logger.info("Disconnecting target container %s from network %s", target_id, net_name)
                                        net.disconnect(target_id, force=force)
                                        logger.info("Disconnected %s from %s", target_id, net_name)
                                    except Exception as e:
                                        logger.warning("Failed to disconnect target container %s from %s: %s", target_id, net_name, e)
                                logger.info("Network %s has active endpoints; skipping removal. endpoints=%s", net_name, list(containers_attached.keys()))
                            except Exception as e:
                                logger.debug("Could not process network endpoints for %s: %s", net_name, e)
                        else:
                            try:
                                net.remove()
                                logger.info("Network %s removed.", net_name)
                            except Exception as e:
                                logger.warning("Network %s removal failed (no active endpoints): %s", net_name, e)
                    except NotFound:
                        logger.debug("Network %s not found.", net_name)
                    except Exception as e:
                        logger.warning("Network lookup/removal error for %s: %s", net_name, e)

                if errors:
                    msg = "Delete completed with errors: " + "; ".join(errors)
                    logger.error(msg)
                    raise Exception(msg)

        except Exception as e:
            logger.exception(
                "container_delete_error name=%s force=%s backup=%s error=%s",
                self.config.name,
                force,
                backup,
                e,
            )
            raise

        logger.debug(
            "container_delete_complete name=%s force=%s backup=%s",
            self.config.name,
            force,
            backup,
        )



class BaseService:
    def __init__(self, config: ContainerConfig, extra: Optional[Dict[str, str]] = None) -> None:
        self.config = config
        self.extra = extra or {}
        self.manager = ContainerManager(self.config)

    def run(self) -> None:
        logger.debug("container_run_start name=%s", self.config.name)
        try:
            self.manager.start()
            logger.debug("container_run_complete name=%s", self.config.name)
        except Exception as e:
            logger.exception("container_run_error name=%s error=%s", self.config.name, e)
            raise

    def stop(self, timeout: int = 10) -> None:
        logger.debug("container_stop_start name=%s timeout=%s", self.config.name, timeout)
        try:
            self.manager.stop(timeout=timeout)
            logger.debug("container_stop_complete name=%s timeout=%s", self.config.name, timeout)
        except Exception as e:
            logger.exception("container_stop_error name=%s timeout=%s error=%s", self.config.name, timeout, e)
            raise

    def restart(self) -> None:
        logger.debug("container_restart_start name=%s", self.config.name)
        try:
            self.manager.restart()
            logger.debug("container_restart_complete name=%s", self.config.name)
        except Exception as e:
            logger.exception("container_restart_error name=%s error=%s", self.config.name, e)
            raise

    def delete(self, force: bool = False) -> None:
        logger.debug("container_delete_start name=%s force=%s", self.config.name, force)
        try:
            self.manager.delete(force=force)
            logger.debug("container_delete_complete name=%s force=%s", self.config.name, force)
        except Exception as e:
            logger.exception("container_delete_error name=%s force=%s error=%s", self.config.name, force, e)
            raise

    def exec(self, cmd: str) -> Tuple[int, str]:
        logger.debug("container_exec_start name=%s cmd=%s", self.config.name, cmd)

        container = self.manager._get_existing_container()
        if not container:
            logger.error("container_exec_not_running name=%s", self.config.name)
            raise RuntimeError("Container not running")

        try:
            logger.debug("container_exec_run name=%s cmd=%s", self.config.name, cmd)
            exec_res = container.exec_run(cmd, demux=True)

            exit_code = getattr(exec_res, "exit_code", 0)
            logger.debug("container_exec_exitcode name=%s exit_code=%s", self.config.name, exit_code)

            stdout, stderr = (None, None)
            output_bytes = b""
            out = getattr(exec_res, "output", None)

            logger.debug("container_exec_raw_output_type name=%s type=%s", self.config.name, type(out))

            if isinstance(out, tuple):
                stdout, stderr = out
                if stdout:
                    logger.debug("container_exec_stdout_size name=%s size=%s", self.config.name, len(stdout))
                    output_bytes += stdout
                if stderr:
                    logger.debug("container_exec_stderr_size name=%s size=%s", self.config.name, len(stderr))
                    output_bytes += stderr
            elif isinstance(out, (bytes, bytearray)):
                logger.debug("container_exec_output_size name=%s size=%s", self.config.name, len(out))
                output_bytes = out
            else:
                logger.debug("container_exec_output_stringified name=%s", self.config.name)
                output_bytes = str(out).encode("utf-8", errors="ignore")

            result = output_bytes.decode("utf-8", errors="ignore")

            logger.debug(
                "container_exec_complete name=%s exit=%s output_length=%s",
                self.config.name,
                exit_code,
                len(result),
            )

            return int(exit_code), result

        except Exception as e:
            logger.exception("container_exec_error name=%s error=%s", self.config.name, e)
            raise
