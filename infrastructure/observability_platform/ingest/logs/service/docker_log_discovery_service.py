import os
import fnmatch
import yaml
import logging
import threading
from typing import List, Dict, Optional
import docker
from docker.errors import DockerException, APIError
from infrastructure.observability_platform.ingest.application_stdout.model.config_model import LogDiscoveryConfig
from infrastructure.observability_platform.ingest.application_stdout.service.log_discovery_service import AbstractLogDiscoveryService

logger = logging.getLogger(__name__)

class DockerLogDiscoveryService(AbstractLogDiscoveryService):
    TAG = "docker.log.discovery"

    def __init__(self, config: LogDiscoveryConfig):
        self.cfg = config.discovery
        self.output_dir = "infrastructure/observability_platform/ingest/config"
        self.yaml_name = "docker_find_logs_config.yaml"
        self.mirror_dir = os.path.join(self.output_dir, "docker-logs")
        self.client = self.create_docker_client()

    def create_docker_client(self):
        logger.info("%s connect_attempt method=docker_from_env", self.TAG)
        try:
            c = docker.from_env()
            c.ping()
            logger.info("%s connect_ok method=docker_from_env", self.TAG)
            return c
        except DockerException as e:
            logger.warning("%s connect_fail method=docker_from_env error=%s", self.TAG, str(e))
        if "DOCKER_HOST" in os.environ:
            host = os.environ["DOCKER_HOST"]
            logger.info("%s connect_attempt method=env DOCKER_HOST=%s", self.TAG, host)
            try:
                c = docker.from_env()
                c.ping()
                logger.info("%s connect_ok method=env DOCKER_HOST=%s", self.TAG, host)
                return c
            except DockerException as e:
                logger.warning("%s connect_fail method=env error=%s", self.TAG, str(e))
        logger.info("%s connect_attempt method=tcp url=tcp://127.0.0.1:2375", self.TAG)
        try:
            c = docker.DockerClient(base_url="tcp://127.0.0.1:2375")
            c.ping()
            logger.info("%s connect_ok method=tcp url=tcp://127.0.0.1:2375", self.TAG)
            return c
        except DockerException as e:
            logger.error("%s connect_fail method=tcp error=%s", self.TAG, str(e))
            return None

    def discover(self) -> List[str]:
        logger.info("%s start", self.TAG)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.mirror_dir, exist_ok=True)
        files = self.collect_container_log_files()
        meta = {
            "generated_at_utc": __import__("datetime").datetime.utcnow().isoformat(timespec="microseconds") + "Z",
            "generated_by": self.TAG,
            "discovered_docker_logs": files,
        }
        with open(os.path.join(self.output_dir, self.yaml_name), "w", encoding="utf-8") as f:
            yaml.safe_dump(meta, f, sort_keys=False)
        logger.info("%s done count=%d path=%s", self.TAG, len(files), os.path.join(self.output_dir, self.yaml_name))
        return files

    def collect_container_log_files(self) -> List[str]:
        results: List[str] = []
        if not self.client:
            logger.warning("%s skip reason=no_docker_client", self.TAG)
            return results
        try:
            containers = self.client.containers.list(all=True)
        except DockerException as e:
            logger.warning("%s list_fail error=%s", self.TAG, str(e))
            return results
        for c in containers:
            info = self._container_identity(c)
            path = self._resolve_readable_log_path(c)
            if not path:
                path = self._ensure_mirror_running(c, info)
            if not path:
                continue
            if not self._included(path):
                logger.debug("%s exclude_by_include_rules container=%s path=%s", self.TAG, info["name"], path)
                continue
            if self._excluded(path):
                logger.debug("%s exclude_by_exclude_rules container=%s path=%s", self.TAG, info["name"], path)
                continue
            final_path = os.path.realpath(path) if self.cfg.follow_symlinks else path
            results.append(final_path)
            logger.info("%s discovered container=%s path=%s", self.TAG, info["name"], final_path)
        return sorted(set(results))

    def _container_identity(self, container) -> Dict[str, str]:
        try:
            name = (container.name or "").strip() or (container.attrs.get("Name", "").lstrip("/") if container.attrs else "")
        except Exception:
            name = ""
        short_id = getattr(container, "short_id", "") or (container.id[:12] if getattr(container, "id", "") else "")
        return {"name": name, "id": short_id}

    def _docker_jsonfile_path(self, container) -> Optional[str]:
        try:
            cid = container.id
            base = "/var/lib/docker/containers"
            p = os.path.join(base, cid, f"{cid}-json.log")
            return p
        except Exception:
            return None

    def _resolve_readable_log_path(self, container) -> Optional[str]:
        try:
            attrs = container.attrs or {}
            host_cfg = attrs.get("HostConfig", {})
            log_cfg = host_cfg.get("LogConfig", {})
            driver = (log_cfg.get("Type") or "").strip()
        except APIError:
            driver = ""
        except Exception:
            driver = ""
        if driver != "json-file":
            return None
        lp = self._docker_jsonfile_path(container)
        if not lp:
            return None
        if not os.path.isfile(lp):
            return None
        if not os.access(lp, os.R_OK):
            logger.debug("%s unreadable path=%s", self.TAG, lp)
            return None
        return lp

    def _mirror_target_path(self, info: Dict[str, str]) -> str:
        safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in (info["name"] or "container"))
        return os.path.join(self.mirror_dir, f"{safe_name}-{info['id']}.log")

    def _ensure_mirror_running(self, container, info: Dict[str, str]) -> Optional[str]:
        target = self._mirror_target_path(info)
        if not self._has_mirror_thread(info["id"]):
            t = threading.Thread(target=self._mirror_worker, args=(container, target, info), daemon=True)
            t.start()
            self._register_mirror_thread(info["id"], t)
            logger.info("%s mirror_started container=%s file=%s", self.TAG, info["name"], target)
        return target

    def _mirror_worker(self, container, target_path: str, info: Dict[str, str]):
        try:
            f = open(target_path, "a", encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.warning("%s mirror_open_fail container=%s file=%s error=%s", self.TAG, info["name"], target_path, str(e))
            return

        try:
            for chunk in container.logs(stream=True, follow=True, tail=0):
                try:
                    if isinstance(chunk, bytes):
                        line = chunk.decode("utf-8", errors="ignore")
                    else:
                        line = str(chunk)
                    f.write(line if line.endswith("\n") else line + "\n")
                    f.flush()
                except Exception:
                    pass

        except Exception as e:
            logger.warning("%s mirror_stream_end container=%s error=%s", self.TAG, info["name"], str(e))

        finally:
            try:
                f.close()
            except Exception:
                pass

    def _included(self, path: str) -> bool:
        name = os.path.basename(path)
        if not self.cfg.include_patterns:
            return True
        for pat in self.cfg.include_patterns:
            if fnmatch.fnmatch(name, pat):
                return True
        return False

    def _excluded(self, path: str) -> bool:
        name = os.path.basename(path)
        for pat in self.cfg.exclude_patterns:
            if fnmatch.fnmatch(name, pat):
                return True
        return False

    def _register_mirror_thread(self, key: str, thread: threading.Thread):
        if not hasattr(self, "mirror_threads"):
            self.mirror_threads: Dict[str, threading.Thread] = {}
        self.mirror_threads[key] = thread

    def _has_mirror_thread(self, key: str) -> bool:
        if not hasattr(self, "mirror_threads"):
            self.mirror_threads = {}
            return False
        t = self.mirror_threads.get(key)
        return bool(t and t.is_alive())
