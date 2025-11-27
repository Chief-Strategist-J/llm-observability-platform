from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Tuple, TYPE_CHECKING
from enum import Enum
from pathlib import Path
import logging
import time
import concurrent.futures
import re
import os
import yaml

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


# ==================== YAML Configuration Support ====================

def substitute_env_vars(text: str, env_dict: Dict[str, str]) -> str:
    """
    Substitute environment variables in the format ${VAR_NAME} with values from env_dict.
    
    Args:
        text: String potentially containing ${VAR_NAME} placeholders
        env_dict: Dictionary of variable names to values
        
    Returns:
        String with all ${VAR_NAME} replaced with corresponding values
    """
    if not isinstance(text, str):
        return text
    
    pattern = r'\$\{([^}]+)\}'
    
    def replacer(match):
        var_name = match.group(1)
        value = env_dict.get(var_name, os.environ.get(var_name, match.group(0)))
        logger.debug("env_var_substitute var=%s value=%s", var_name, value)
        return str(value)
    
    result = re.sub(pattern, replacer, text)
    return result


def substitute_env_in_structure(data: Any, env_dict: Dict[str, str]) -> Any:
    """
    Recursively substitute environment variables in nested structures (dicts, lists, strings).
    
    Args:
        data: Data structure (dict, list, str, etc.)
        env_dict: Dictionary of variable names to values
        
    Returns:
        Data structure with all environment variables substituted
    """
    if isinstance(data, dict):
        return {k: substitute_env_in_structure(v, env_dict) for k, v in data.items()}
    elif isinstance(data, list):
        return [substitute_env_in_structure(item, env_dict) for item in data]
    elif isinstance(data, str):
        return substitute_env_vars(data, env_dict)
    else:
        return data


def parse_memory_string(mem_str: Optional[str]) -> Optional[str]:
    """
    Parse memory string in Docker Compose format (e.g., "512m", "1g") and return as-is.
    Docker SDK accepts these formats directly.
    
    Args:
        mem_str: Memory string like "512m", "1g", "2048000000"
        
    Returns:
        Memory string suitable for Docker SDK
    """
    if not mem_str:
        return None
    return str(mem_str)


def parse_cpu_string(cpu_str: Optional[Union[str, float]]) -> Optional[int]:
    """
    Parse CPU string/float and convert to nano_cpus for Docker SDK.
    
    Args:
        cpu_str: CPU value like "0.5", "1.0", or 0.5
        
    Returns:
        Integer nano_cpus value (cpus * 1_000_000_000)
    """
    if cpu_str is None or cpu_str == "":
        return None
    
    try:
        cpu_float = float(cpu_str)
        if cpu_float > 0:
            return int(cpu_float * 1_000_000_000)
    except (ValueError, TypeError) as e:
        logger.warning("parse_cpu_invalid value=%s error=%s", cpu_str, e)
    
    return None


@dataclass
class YAMLContainerConfig:
    """
    Container configuration parsed from a YAML file (Docker Compose format).
    """
    service_name: str
    image: str
    container_name: str
    ports: Dict[str, str] = field(default_factory=dict)
    volumes: List[Union[str, Dict[str, Any]]] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    networks: List[str] = field(default_factory=list)
    command: Optional[Union[str, List[str]]] = None
    entrypoint: Optional[Union[str, List[str]]] = None
    working_dir: Optional[str] = None
    user: Optional[str] = None
    hostname: Optional[str] = None
    domainname: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    restart: str = "unless-stopped"
    healthcheck: Optional[Dict[str, Any]] = None
    deploy: Optional[Dict[str, Any]] = None
    depends_on: List[str] = field(default_factory=list)
    privileged: bool = False
    cap_add: List[str] = field(default_factory=list)
    cap_drop: List[str] = field(default_factory=list)
    devices: List[str] = field(default_factory=list)
    dns: List[str] = field(default_factory=list)
    dns_search: List[str] = field(default_factory=list)
    extra_hosts: Dict[str, str] = field(default_factory=dict)
    security_opt: List[str] = field(default_factory=list)
    tmpfs: Union[List[str], Dict[str, str]] = field(default_factory=list)
    sysctls: Dict[str, str] = field(default_factory=dict)
    ulimits: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_yaml_service(cls, service_name: str, service_data: Dict[str, Any]) -> "YAMLContainerConfig":
        """
        Create a YAMLContainerConfig from a service definition in Docker Compose YAML.
        
        Args:
            service_name: Name of the service
            service_data: Service configuration dict from YAML
            
        Returns:
            YAMLContainerConfig instance
        """
        logger.debug("yaml_config_parse service=%s", service_name)
        
        return cls(
            service_name=service_name,
            image=service_data.get("image", ""),
            container_name=service_data.get("container_name", service_name),
            ports=cls._parse_ports(service_data.get("ports", [])),
            volumes=service_data.get("volumes", []),
            environment=cls._parse_environment(service_data.get("environment", {})),
            networks=cls._parse_networks(service_data.get("networks", [])),
            command=service_data.get("command"),
            entrypoint=service_data.get("entrypoint"),
            working_dir=service_data.get("working_dir"),
            user=service_data.get("user"),
            hostname=service_data.get("hostname"),
            domainname=service_data.get("domainname"),
            labels=service_data.get("labels", {}),
            restart=service_data.get("restart", "unless-stopped"),
            healthcheck=service_data.get("healthcheck"),
            deploy=service_data.get("deploy"),
            depends_on=cls._parse_depends_on(service_data.get("depends_on", [])),
            privileged=service_data.get("privileged", False),
            cap_add=service_data.get("cap_add", []),
            cap_drop=service_data.get("cap_drop", []),
            devices=service_data.get("devices", []),
            dns=service_data.get("dns", []),
            dns_search=service_data.get("dns_search", []),
            extra_hosts=service_data.get("extra_hosts", {}),
            security_opt=service_data.get("security_opt", []),
            tmpfs=service_data.get("tmpfs", []),
            sysctls=service_data.get("sysctls", {}),
            ulimits=service_data.get("ulimits", {}),
        )
    
    @staticmethod
    def _parse_ports(ports: Union[List, Dict]) -> Dict[str, str]:
        """Parse ports from Docker Compose format to dict."""
        if isinstance(ports, dict):
            return ports
        
        port_dict = {}
        for port_spec in ports:
            if isinstance(port_spec, str):
                # Format: "host:container" or "port"
                parts = port_spec.split(":")
                if len(parts) == 2:
                    port_dict[parts[1]] = parts[0]
                elif len(parts) == 1:
                    port_dict[parts[0]] = parts[0]
            elif isinstance(port_spec, dict):
                # Long format: {target: 80, published: 8080}
                target = str(port_spec.get("target", ""))
                published = str(port_spec.get("published", target))
                if target:
                    port_dict[target] = published
        
        return port_dict
    
    @staticmethod
    def _parse_environment(env: Union[Dict, List]) -> Dict[str, str]:
        """Parse environment from Docker Compose format to dict."""
        if isinstance(env, dict):
            return {k: str(v) for k, v in env.items()}
        
        env_dict = {}
        for item in env:
            if isinstance(item, str):
                if "=" in item:
                    key, value = item.split("=", 1)
                    env_dict[key] = value
                else:
                    env_dict[item] = ""
        
        return env_dict
    
    @staticmethod
    def _parse_networks(networks: Union[List, Dict]) -> List[str]:
        """Parse networks from Docker Compose format to list."""
        if isinstance(networks, list):
            return networks
        elif isinstance(networks, dict):
            return list(networks.keys())
        return []
    
    @staticmethod
    def _parse_depends_on(depends: Union[List, Dict]) -> List[str]:
        """Parse depends_on from Docker Compose format to list."""
        if isinstance(depends, list):
            return depends
        elif isinstance(depends, dict):
            return list(depends.keys())
        return []


class YAMLConfigLoader:
    """
    Loader for Docker Compose YAML configuration files with environment variable substitution.
    """
    
    def __init__(self):
        logger.debug("yaml_loader_init")
    
    def load_yaml_file(self, file_path: Union[str, Path], env_vars: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Load a Docker Compose YAML file and substitute environment variables.
        
        Args:
            file_path: Path to the YAML configuration file
            env_vars: Dictionary of environment variables for substitution
            
        Returns:
            Parsed YAML data with environment variables substituted
        """
        file_path = Path(file_path)
        logger.debug("yaml_load_start file=%s", file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"YAML file not found: {file_path}")
        
        # Read YAML file
        with open(file_path, 'r') as f:
            yaml_content = f.read()
        
        # Substitute environment variables in the raw YAML string first
        env_dict = env_vars or {}
        yaml_content = substitute_env_vars(yaml_content, env_dict)
        
        # Parse YAML
        try:
            yaml_data = yaml.safe_load(yaml_content)
            logger.debug("yaml_load_parsed file=%s services=%s", file_path, len(yaml_data.get("services", {})))
        except yaml.YAMLError as e:
            logger.exception("yaml_load_error file=%s error=%s", file_path, e)
            raise
        
        # Additional recursive substitution for nested structures
        yaml_data = substitute_env_in_structure(yaml_data, env_dict)
        
        logger.debug("yaml_load_complete file=%s", file_path)
        return yaml_data
    
    def parse_service(self, service_name: str, yaml_data: Dict[str, Any]) -> YAMLContainerConfig:
        """
        Parse a specific service from loaded YAML data.
        
        Args:
            service_name: Name of the service to parse
            yaml_data: Complete parsed YAML data
            
        Returns:
            YAMLContainerConfig for the specified service
        """
        logger.debug("yaml_parse_service service=%s", service_name)
        
        services = yaml_data.get("services", {})
        if service_name not in services:
            raise ValueError(f"Service '{service_name}' not found in YAML. Available: {list(services.keys())}")
        
        service_data = services[service_name]
        config = YAMLContainerConfig.from_yaml_service(service_name, service_data)
        
        logger.debug("yaml_parse_service_complete service=%s container=%s", service_name, config.container_name)
        return config
    
    def get_networks(self, yaml_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Extract network definitions from YAML data.
        
        Args:
            yaml_data: Complete parsed YAML data
            
        Returns:
            Dictionary of network configurations
        """
        return yaml_data.get("networks", {})
    
    def get_volumes(self, yaml_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Extract volume definitions from YAML data.
        
        Args:
            yaml_data: Complete parsed YAML data
            
        Returns:
            Dictionary of volume configurations
        """
        return yaml_data.get("volumes", {})


# ==================== Container Management ====================

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
        volumes: Union[List, Dict[str, Union[str, Tuple[str, str], List[Any], Dict[str, Any]]]]
    ) -> Dict[str, Dict[str, str]]:
        """
        Normalize volumes from various formats to Docker SDK format.
        
        Supports:
        - List format: ["/host:/container", "/host:/container:ro"]
        - Dict format: {"/host": "/container"} or {"/host": {"bind": "/container", "mode": "rw"}}
        """
        logger.debug("volume_normalize_start volumes_count=%s", len(volumes) if volumes else 0)
        normalized: Dict[str, Dict[str, str]] = {}

        try:
            # Handle list format (Docker Compose style)
            if isinstance(volumes, list):
                for vol_spec in volumes:
                    if isinstance(vol_spec, str):
                        # Format: "/host:/container" or "/host:/container:mode"
                        parts = vol_spec.split(":")
                        if len(parts) >= 2:
                            host = parts[0]
                            container = parts[1]
                            mode = parts[2] if len(parts) > 2 else "rw"
                            normalized[host] = {"bind": container, "mode": mode}
                            logger.debug("volume_normalize_list_str host=%s bind=%s mode=%s", host, container, mode)
                    elif isinstance(vol_spec, dict):
                        # Long format: {type: volume, source: name, target: /path}
                        source = vol_spec.get("source", "")
                        target = vol_spec.get("target", "")
                        mode = vol_spec.get("read_only", False)
                        if source and target:
                            normalized[source] = {"bind": target, "mode": "ro" if mode else "rw"}
                            logger.debug("volume_normalize_list_dict source=%s target=%s", source, target)
                return normalized
            
            # Handle dict format (original ContainerConfig style)
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

            if not isinstance(raw, (dict, list)):
                raise TypeError(f"'volumes' run-arg must be a dict or list; got {type(raw).__name__}")

            if isinstance(raw, dict) and all(isinstance(v, dict) and "bind" in v for v in raw.values()):
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


class YAMLContainerManager(BaseContainerManager):
    """
    Container manager that works with YAML-based configuration.
    """
    
    def __init__(self, config: YAMLContainerConfig) -> None:
        self.config = config
        self.client = self.get_docker_client()
        self.container: Optional["Container"] = None
        
        logger.debug("yaml_manager_init container=%s image=%s", self.config.container_name, self.config.image)
    
    def _ensure_image_exists(self) -> None:
        from docker.errors import ImageNotFound, DockerException  # type: ignore

        logger.debug("image_check_start name=%s image=%s", self.config.container_name, self.config.image)
        try:
            self.client.images.get(self.config.image)
            logger.debug("image_check_exists name=%s image=%s", self.config.container_name, self.config.image)
        except ImageNotFound:
            logger.debug("image_check_missing name=%s image=%s", self.config.container_name, self.config.image)
            try:
                self._pull_image()
            except Exception as e:
                logger.exception("image_check_pull_error name=%s image=%s error=%s", self.config.container_name, self.config.image, e)
                raise
        except DockerException as e:
            logger.exception("image_check_error name=%s image=%s error=%s", self.config.container_name, self.config.image, e)
            raise
        logger.debug("image_check_complete name=%s image=%s", self.config.container_name, self.config.image)

    def _pull_image(self, retry_attempts: int = 3, pull_timeout: int = 300) -> None:
        attempts = max(1, int(retry_attempts))
        logger.debug("image_pull_start name=%s image=%s attempts=%s", self.config.container_name, self.config.image, attempts)

        last_exc: Optional[Exception] = None
        for attempt in range(1, attempts + 1):
            logger.debug("image_pull_attempt_start name=%s image=%s attempt=%s", self.config.container_name, self.config.image, attempt)
            try:
                if pull_timeout and pull_timeout > 0:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                        future = ex.submit(self.client.images.pull, self.config.image)
                        try:
                            future.result(timeout=pull_timeout)
                        except concurrent.futures.TimeoutError as te:
                            logger.debug("image_pull_timeout name=%s image=%s timeout=%s attempt=%s",
                                         self.config.container_name, self.config.image, pull_timeout, attempt)
                            raise TimeoutError(f"Image pull timed out after {pull_timeout}s") from te
                else:
                    self.client.images.pull(self.config.image)

                logger.info("Successfully pulled image %s", self.config.image)
                logger.debug("image_pull_attempt_success name=%s image=%s attempt=%s",
                             self.config.container_name, self.config.image, attempt)
                return

            except Exception as exc:
                last_exc = exc
                logger.debug("image_pull_attempt_error name=%s image=%s attempt=%s error=%s",
                             self.config.container_name, self.config.image, attempt, exc)
                time.sleep(2 * attempt)

        logger.error("Failed to pull image %s after %d attempts", self.config.image, attempts)
        logger.debug("image_pull_failed name=%s image=%s attempts=%s", self.config.container_name, self.config.image, attempts)

        if last_exc:
            raise last_exc
        raise RuntimeError("Unknown error pulling image")

    def _ensure_networks_exist(self) -> None:
        """Ensure all networks required by the container exist."""
        from docker.errors import NotFound, DockerException
        
        for net_name in self.config.networks:
            if not net_name or net_name in ("bridge", "host", "none"):
                logger.debug("Skipping built-in network: %s", net_name)
                continue
            
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
    
    def _ensure_container_on_networks(self, container):
        """Attach container to all configured networks."""
        try:
            for net_name in self.config.networks:
                if not net_name or net_name in ("bridge", "host", "none"):
                    logger.debug("No external network required for %s", self.config.container_name)
                    continue
                
                net = self.client.networks.get(net_name)
                container.reload()
                networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})
                
                if net_name in networks:
                    logger.debug("Container %s already attached to %s", self.config.container_name, net_name)
                    continue
                
                logger.info("Attaching container %s to network %s", self.config.container_name, net_name)
                net.connect(container)
                logger.info("Container %s attached to network %s", self.config.container_name, net_name)
        except Exception as e:
            logger.exception("Network attach failed for %s: %s", self.config.container_name, e)
    
    def _convert_healthcheck(self, healthcheck: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Docker Compose healthcheck format to Docker SDK format.
        
        Compose format:
          test: ["CMD-SHELL", "curl -f http://localhost"]
          interval: 30s
          timeout: 10s
          retries: 3
          start_period: 40s
          
        SDK format:
          test: ["CMD-SHELL", "curl -f http://localhost"]
          interval: 30000000000  # nanoseconds
          timeout: 10000000000
          retries: 3
          start_period: 40000000000
        """
        if not healthcheck:
            return {}
        
        def parse_duration(duration_str: str) -> int:
            """Parse duration string like '30s', '1m' to nanoseconds."""
            if not duration_str:
                return 0
            
            duration_str = str(duration_str).strip()
            
            # If already a number, assume it's in nanoseconds
            if duration_str.isdigit():
                return int(duration_str)
            
            # Parse formats like "30s", "1m", "1h"
            import re
            match = re.match(r'(\d+)([smh]?)', duration_str)
            if match:
                value = int(match.group(1))
                unit = match.group(2) or 's'
                
                if unit == 's':
                    return value * 1_000_000_000
                elif unit == 'm':
                    return value * 60 * 1_000_000_000
                elif unit == 'h':
                    return value * 3600 * 1_000_000_000
            
            return 0
        
        sdk_healthcheck = {}
        
        if "test" in healthcheck:
            sdk_healthcheck["test"] = healthcheck["test"]
        
        if "interval" in healthcheck:
            sdk_healthcheck["interval"] = parse_duration(healthcheck["interval"])
        
        if "timeout" in healthcheck:
            sdk_healthcheck["timeout"] = parse_duration(healthcheck["timeout"])
        
        if "retries" in healthcheck:
            sdk_healthcheck["retries"] = int(healthcheck["retries"])
        
        if "start_period" in healthcheck:
            sdk_healthcheck["start_period"] = parse_duration(healthcheck["start_period"])
        
        logger.debug("healthcheck_converted original=%s sdk=%s", healthcheck, sdk_healthcheck)
        return sdk_healthcheck
    
    def _convert_ports(self, ports: Dict[str, str]) -> Dict[str, int]:
        """
        Convert ports from string dict to proper Docker SDK format.
        
        Args:
            ports: Dict like {"6379": "6379"} or {"6379/tcp": "6379"}
            
        Returns:
            Dict like {"6379/tcp": 6379} suitable for Docker SDK
        """
        converted = {}
        for container_port, host_port in ports.items():
            # Ensure container port has protocol
            if "/" not in container_port:
                container_port = f"{container_port}/tcp"
            
            # Convert host port to int
            try:
                converted[container_port] = int(host_port)
            except (ValueError, TypeError):
                logger.warning("Invalid port value: %s -> %s", container_port, host_port)
        
        return converted
    
    def _get_resource_limits(self) -> Dict[str, Any]:
        """Extract resource limits from deploy configuration."""
        resources = {}
        
        if not self.config.deploy:
            return resources
        
        deploy_resources = self.config.deploy.get("resources", {})
        limits = deploy_resources.get("limits", {})
        reservations = deploy_resources.get("reservations", {})
        
        # Memory limits
        if "memory" in limits:
            resources["mem_limit"] = parse_memory_string(limits["memory"])
        
        if "memory" in reservations:
            resources["mem_reservation"] = parse_memory_string(reservations["memory"])
        
        # CPU limits
        if "cpus" in limits:
            nano_cpus = parse_cpu_string(limits["cpus"])
            if nano_cpus:
                resources["nano_cpus"] = nano_cpus
        
        logger.debug("resource_limits_extracted resources=%s", resources)
        return resources

    def start(self) -> None:
        from docker.errors import DockerException, NotFound
        logger.debug("Starting container: %s", self.config.container_name)
        
        try:
            existing = self._get_existing_container()
            
            try:
                self._ensure_networks_exist()
            except Exception:
                logger.warning("Network ensure step failed; continuing start")

            if existing:
                logger.info("Container %s already exists; starting.", self.config.container_name)
                try:
                    existing.start()
                    self._ensure_container_on_networks(existing)
                    self.container = existing
                    return
                except DockerException as start_exc:
                    msg = str(start_exc).lower()
                    if "network" in msg and "not found" in msg:
                        logger.warning("Start failed due to missing network; recreating")
                        self._ensure_networks_exist()
                        existing.start()
                        self._ensure_container_on_networks(existing)
                        self.container = existing
                        return
                    logger.exception("Failed to start existing container %s: %s", self.config.container_name, start_exc)
                    raise

            self._ensure_image_exists()

            # Build Docker SDK run arguments
            run_args = {
                "image": self.config.image,
                "name": self.config.container_name,
                "detach": True,
                "restart_policy": {"Name": self.config.restart},
            }

            def add_arg(k, v):
                if v not in (None, {}, [], ""):
                    run_args[k] = v

            # Ports
            if self.config.ports:
                run_args["ports"] = self._convert_ports(self.config.ports)
            
            # Volumes
            if self.config.volumes:
                add_arg("volumes", self._normalize_volumes_for_docker(self.config.volumes))
            
            # Environment
            add_arg("environment", self.config.environment)
            
            # Labels
            add_arg("labels", self.config.labels)
            
            # Command and entrypoint
            add_arg("command", self.config.command)
            add_arg("entrypoint", self.config.entrypoint)
            
            # Working directory and user
            add_arg("working_dir", self.config.working_dir)
            add_arg("user", self.config.user)
            
            # Network (primary network)
            if self.config.networks:
                add_arg("network", self.config.networks[0])
            
            # Hostname and domain
            add_arg("hostname", self.config.hostname)
            add_arg("domainname", self.config.domainname)
            
            # DNS settings
            add_arg("dns", self.config.dns)
            add_arg("dns_search", self.config.dns_search)
            add_arg("extra_hosts", self.config.extra_hosts)
            
            # Resource limits from deploy section
            resource_limits = self._get_resource_limits()
            run_args.update(resource_limits)
            
            # Security and privileges
            add_arg("privileged", self.config.privileged)
            add_arg("cap_add", self.config.cap_add)
            add_arg("cap_drop", self.config.cap_drop)
            add_arg("devices", self.config.devices)
            add_arg("security_opt", self.config.security_opt)
            
            # Tmpfs and sysctls
            add_arg("tmpfs", self.config.tmpfs)
            add_arg("sysctls", self.config.sysctls)
            
            # Healthcheck
            if self.config.healthcheck:
                run_args["healthcheck"] = self._convert_healthcheck(self.config.healthcheck)

            self._validate_and_normalize_volumes_in_run_args(run_args)

            debug_args = {k: v for k, v in run_args.items() if k not in ("environment", "labels", "volumes")}
            logger.debug("Calling containers.run args: %s", debug_args)

            try:
                self.container = self.client.containers.run(**run_args)
                self._ensure_container_on_networks(self.container)
                logger.info("Container %s created & started.", self.config.container_name)
            except DockerException as run_exc:
                msg = str(run_exc).lower()
                if "network" in msg and "not found" in msg:
                    logger.warning("Run failed due to network missing; recreating network")
                    self._ensure_networks_exist()
                    try:
                        self.container = self.client.containers.get(self.config.container_name)
                        self.container.start()
                        self._ensure_container_on_networks(self.container)
                        logger.info("Container %s started after recreate.", self.config.container_name)
                        return
                    except Exception as second_exc:
                        logger.exception("Retry after network create failed: %s", second_exc)
                        raise
                logger.exception("containers.run failed: %s", run_exc)
                raise

        except Exception as de:
            logger.exception("Error when starting container %s: %s", self.config.container_name, de)
            raise

    def stop(self, timeout: int = 10) -> None:
        logger.debug("container_stop_start name=%s timeout=%s", self.config.container_name, timeout)
        try:
            container = self._get_existing_container()
            if container:
                try:
                    container.stop(timeout=timeout)
                    logger.info("Container %s stopped.", self.config.container_name)
                except Exception as e:
                    logger.exception("container_stop_error name=%s timeout=%s error=%s", self.config.container_name, timeout, e)
                    raise
            else:
                logger.debug("container_stop_notfound name=%s", self.config.container_name)
        except Exception as e:
            logger.exception("container_stop_wrapper_error name=%s error=%s", self.config.container_name, e)
            raise
        logger.debug("container_stop_complete name=%s timeout=%s", self.config.container_name, timeout)

    def restart(self) -> None:
        logger.debug("container_restart_start name=%s", self.config.container_name)
        try:
            container = self._get_existing_container()
            if container:
                try:
                    container.restart()
                    logger.info("Container %s restarted.", self.config.container_name)
                except Exception as e:
                    logger.exception("container_restart_error name=%s error=%s", self.config.container_name, e)
                    raise
            else:
                logger.debug("container_restart_notfound name=%s", self.config.container_name)
        except Exception as e:
            logger.exception("container_restart_wrapper_error name=%s error=%s", self.config.container_name, e)
            raise
        logger.debug("container_restart_complete name=%s", self.config.container_name)

    def logs(self, follow: bool = False) -> str:
        logger.debug("container_logs_fetch_start name=%s follow=%s", self.config.container_name, follow)
        try:
            container = self._get_existing_container()
            if not container:
                logger.debug("container_logs_not_found name=%s", self.config.container_name)
                return ""

            logs_bytes = container.logs(follow=follow)
            logger.debug(
                "container_logs_fetch_complete name=%s type=%s",
                self.config.container_name,
                type(logs_bytes),
            )

            if isinstance(logs_bytes, (bytes, bytearray)):
                return logs_bytes.decode("utf-8", errors="ignore")

            return str(logs_bytes)

        except Exception as e:
            logger.exception("container_logs_error name=%s error=%s", self.config.container_name, e)
            raise

    def _get_existing_container(self) -> Optional["Container"]:
        from docker.errors import NotFound  # type: ignore
        logger.debug("container_lookup_start name=%s", self.config.container_name)
        try:
            container = self.client.containers.get(self.config.container_name)
            logger.debug("container_lookup_found name=%s", self.config.container_name)
            return container
        except NotFound:
            logger.debug("container_lookup_notfound name=%s", self.config.container_name)
            return None
        except Exception as e:
            logger.exception("container_lookup_error name=%s error=%s", self.config.container_name, e)
            raise

    def delete(self, force: bool = False, backup: bool = False) -> None:
        logger.debug(
            "container_delete_start name=%s force=%s backup=%s",
            self.config.container_name,
            force,
            backup,
        )

        import threading
        import datetime
        from docker.errors import ImageNotFound, NotFound

        try:
            if not hasattr(self, "_delete_lock"):
                self._delete_lock = threading.RLock()

            with self._delete_lock:
                logger.debug(
                    "container_delete_lock_acquired name=%s",
                    self.config.container_name,
                )

                container = self._get_existing_container()
                if not container:
                    logger.debug(
                        "container_delete_container_missing name=%s",
                        self.config.container_name,
                    )
                    return

                errors: list[str] = []
                ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                backup_dir = Path(os.getcwd()) / "container_backups"
                backup_dir.mkdir(parents=True, exist_ok=True)

                logger.debug(
                    "container_delete_initialized name=%s timestamp=%s backup_dir=%s",
                    self.config.container_name,
                    ts,
                    backup_dir,
                )

                try:
                    try:
                        container.reload()
                        logger.debug("container_delete_reload_ok name=%s", self.config.container_name)
                    except Exception:
                        logger.debug("container_delete_reload_failed name=%s", self.config.container_name)

                    if backup:
                        logger.debug("container_delete_backup_start name=%s", self.config.container_name)
                        try:
                            if getattr(container, "status", "") == "running":
                                try:
                                    container.stop(timeout=30)
                                    logger.debug("container_delete_backup_stopped name=%s", self.config.container_name)
                                except Exception as e:
                                    if force:
                                        try:
                                            container.kill()
                                            logger.debug("container_delete_backup_killed name=%s", self.config.container_name)
                                        except Exception:
                                            logger.debug("container_delete_backup_kill_failed name=%s", self.config.container_name)
                                    else:
                                        raise
                            export_name = backup_dir / f"{self.config.container_name}_export_{ts}.tar"
                            with export_name.open("wb") as f:
                                for chunk in container.export():
                                    f.write(chunk)
                            logger.info("Wrote container export %s", export_name)
                        except Exception as e:
                            logger.exception(
                                "container_delete_backup_export_failed name=%s error=%s",
                                self.config.container_name,
                                e,
                            )
                            raise

                        try:
                            image_repo = f"{self.config.container_name}_backup"
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

                            save_name = backup_dir / f"{self.config.container_name}_image_{ts}.tar"
                            with save_name.open("wb") as f:
                                for chunk in image_obj.save(named=True):
                                    f.write(chunk)
                            logger.info("Wrote image backup %s", save_name)
                        except Exception as e:
                            logger.exception(
                                "container_delete_backup_image_failed name=%s error=%s",
                                self.config.container_name,
                                e,
                            )
                            raise

                except Exception as e:
                    logger.debug(
                        "container_delete_backup_ops_error name=%s error=%s",
                        self.config.container_name,
                        e,
                    )
                    raise

                try:
                    try:
                        container.reload()
                        logger.debug("container_delete_reload2_ok name=%s", self.config.container_name)
                    except Exception:
                        logger.debug("container_delete_reload2_failed name=%s", self.config.container_name)

                    if getattr(container, "status", "") == "running":
                        try:
                            container.stop(timeout=30)
                            logger.info("Container %s stopped.", self.config.container_name)
                        except Exception as e:
                            if force:
                                try:
                                    container.kill()
                                    logger.debug("container_delete_killed name=%s", self.config.container_name)
                                except Exception as e2:
                                    errors.append(f"kill: {e2}")
                            else:
                                errors.append(f"stop: {e}")

                    try:
                        container.remove(force=force)
                        logger.info("Container %s removed.", self.config.container_name)
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

                # Remove networks
                for net_name in self.config.networks:
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
                self.config.container_name,
                force,
                backup,
                e,
            )
            raise

        logger.debug(
            "container_delete_complete name=%s force=%s backup=%s",
            self.config.container_name,
            force,
            backup,
        )


# ==================== Service Classes ====================

class YAMLBaseService:
    """
    Base service class that loads configuration from YAML files.
    """
    
    def __init__(
        self,
        yaml_file_path: Union[str, Path],
        service_name: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        instance_id: Optional[str] = None
    ) -> None:
        """
        Initialize service from YAML configuration.
        
        Args:
            yaml_file_path: Path to Docker Compose YAML file
            service_name: Name of the service in the YAML file (if None, uses first service)
            env_vars: Additional environment variables for substitution
            instance_id: Instance ID for multi-instance deployments
        """
        self.yaml_file_path = Path(yaml_file_path)
        self.instance_id = instance_id or "1"
        
        # Prepare environment variables
        self.env_vars = env_vars or {}
        if instance_id:
            self.env_vars["INSTANCE_ID"] = instance_id
        
        logger.debug("yaml_service_init file=%s instance=%s", yaml_file_path, self.instance_id)
        
        # Load and parse YAML
        loader = YAMLConfigLoader()
        yaml_data = loader.load_yaml_file(self.yaml_file_path, self.env_vars)
        
        # Determine service name
        services = yaml_data.get("services", {})
        if not services:
            raise ValueError(f"No services found in YAML file: {yaml_file_path}")
        
        if service_name is None:
            service_name = list(services.keys())[0]
            logger.debug("yaml_service_auto_select service=%s", service_name)
        
        # Parse service configuration
        self.config = loader.parse_service(service_name, yaml_data)
        self.manager = YAMLContainerManager(self.config)
        
        logger.info("yaml_service_initialized service=%s container=%s", service_name, self.config.container_name)
    
    def run(self) -> None:
        logger.debug("container_run_start name=%s", self.config.container_name)
        try:
            self.manager.start()
            logger.debug("container_run_complete name=%s", self.config.container_name)
        except Exception as e:
            logger.exception("container_run_error name=%s error=%s", self.config.container_name, e)
            raise

    def stop(self, timeout: int = 10) -> None:
        logger.debug("container_stop_start name=%s timeout=%s", self.config.container_name, timeout)
        try:
            self.manager.stop(timeout=timeout)
            logger.debug("container_stop_complete name=%s timeout=%s", self.config.container_name, timeout)
        except Exception as e:
            logger.exception("container_stop_error name=%s timeout=%s error=%s", self.config.container_name, timeout, e)
            raise

    def restart(self) -> None:
        logger.debug("container_restart_start name=%s", self.config.container_name)
        try:
            self.manager.restart()
            logger.debug("container_restart_complete name=%s", self.config.container_name)
        except Exception as e:
            logger.exception("container_restart_error name=%s error=%s", self.config.container_name, e)
            raise

    def delete(self, force: bool = False) -> None:
        logger.debug("container_delete_start name=%s force=%s", self.config.container_name, force)
        try:
            self.manager.delete(force=force)
            logger.debug("container_delete_complete name=%s force=%s", self.config.container_name, force)
        except Exception as e:
            logger.exception("container_delete_error name=%s force=%s error=%s", self.config.container_name, force, e)
            raise

    def logs(self, follow: bool = False) -> str:
        logger.debug("container_logs_start name=%s follow=%s", self.config.container_name, follow)
        try:
            result = self.manager.logs(follow=follow)
            logger.debug("container_logs_complete name=%s", self.config.container_name)
            return result
        except Exception as e:
            logger.exception("container_logs_error name=%s error=%s", self.config.container_name, e)
            raise

    def exec(self, cmd: str) -> Tuple[int, str]:
        logger.debug("container_exec_start name=%s cmd=%s", self.config.container_name, cmd)

        container = self.manager._get_existing_container()
        if not container:
            logger.error("container_exec_not_running name=%s", self.config.container_name)
            raise RuntimeError("Container not running")

        try:
            logger.debug("container_exec_run name=%s cmd=%s", self.config.container_name, cmd)
            exec_res = container.exec_run(cmd, demux=True)

            exit_code = getattr(exec_res, "exit_code", 0)
            logger.debug("container_exec_exitcode name=%s exit_code=%s", self.config.container_name, exit_code)

            stdout, stderr = (None, None)
            output_bytes = b""
            out = getattr(exec_res, "output", None)

            logger.debug("container_exec_raw_output_type name=%s type=%s", self.config.container_name, type(out))

            if isinstance(out, tuple):
                stdout, stderr = out
                if stdout:
                    logger.debug("container_exec_stdout_size name=%s size=%s", self.config.container_name, len(stdout))
                    output_bytes += stdout
                if stderr:
                    logger.debug("container_exec_stderr_size name=%s size=%s", self.config.container_name, len(stderr))
                    output_bytes += stderr
            elif isinstance(out, (bytes, bytearray)):
                logger.debug("container_exec_output_size name=%s size=%s", self.config.container_name, len(out))
                output_bytes = out
            else:
                logger.debug("container_exec_output_stringified name=%s", self.config.container_name)
                output_bytes = str(out).encode("utf-8", errors="ignore")

            result = output_bytes.decode("utf-8", errors="ignore")

            logger.debug(
                "container_exec_complete name=%s exit=%s output_length=%s",
                self.config.container_name,
                exit_code,
                len(result),
            )

            return int(exit_code), result

        except Exception as e:
            logger.exception("container_exec_error name=%s error=%s", self.config.container_name, e)
            raise
