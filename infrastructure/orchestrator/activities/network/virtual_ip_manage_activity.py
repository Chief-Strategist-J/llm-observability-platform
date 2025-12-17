from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from temporalio import activity
import logging
import socket
import subprocess
import time
import yaml
import ipaddress
import re

logger = logging.getLogger(__name__)


@dataclass
class VirtualIPConfig:
    interface: str = "lo"
    ip_base: str = "127.0.2"
    ip_start: int = 1
    ip_end: int = 254
    netmask: str = "255.255.255.0"
    expected_hostname_ip: Optional[str] = None
    hostname_resolution_overrides: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, config_dir: Path) -> "VirtualIPConfig":
        config_path = config_dir / "virtual_ip_config.yaml"
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    data = yaml.safe_load(f) or {}
                return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
            except Exception as e:
                logger.warning("event=config_load_failed path=%s error=%s", config_path, str(e))
        return cls()

    def save(self, config_dir: Path):
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            config_path = config_dir / "virtual_ip_config.yaml"
            with open(config_path, "w") as f:
                yaml.dump(asdict(self), f, default_flow_style=False)
            logger.debug("event=config_saved path=%s", config_path)
        except Exception as e:
            logger.warning("event=config_save_failed error=%s", str(e))


@dataclass
class IPAllocation:
    hostname: str
    ip: str
    allocated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class VirtualIPManager:
    def __init__(self, config: VirtualIPConfig, config_dir: Path):
        self.config = config
        self.config_dir = config_dir
        self.allocations_file = config_dir / "virtual_ip_allocations.yaml"
        self.allocations: Dict[str, IPAllocation] = self.load_allocations()

    def get_expected_hostname_ips(self, hostname: str) -> List[str]:
        expected_ips: List[str] = []
        overrides = self.config.hostname_resolution_overrides or {}
        override = overrides.get(hostname)
        if override:
            expected_ips.append(str(override))

        fallback = self.config.expected_hostname_ip
        if fallback and fallback not in expected_ips:
            expected_ips.append(str(fallback))

        return expected_ips

    def load_allocations(self) -> Dict[str, IPAllocation]:
        if not self.allocations_file.exists():
            return {}
        try:
            with open(self.allocations_file, "r") as f:
                data = yaml.safe_load(f) or {}
            return {k: IPAllocation(**v) for k, v in data.items()}
        except Exception as e:
            logger.warning("event=allocations_load_failed path=%s error=%s", self.allocations_file, str(e))
            return {}

    def save_allocations(self):
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.allocations_file, "w") as f:
                yaml.dump({k: v.to_dict() for k, v in self.allocations.items()}, f, default_flow_style=False)
        except Exception as e:
            logger.warning("event=allocations_save_failed path=%s error=%s", self.allocations_file, str(e))

    def get_next_available_ip(self) -> Optional[str]:
        allocated_ips = {alloc.ip for alloc in self.allocations.values()}
        for i in range(self.config.ip_start, self.config.ip_end + 1):
            candidate = f"{self.config.ip_base}.{i}"
            if candidate not in allocated_ips:
                return candidate
        return None

    def allocate_ip(self, hostname: str, requested_ip: Optional[str] = None) -> Optional[str]:
        if hostname in self.allocations:
            logger.debug("event=ip_already_allocated hostname=%s ip=%s", hostname, self.allocations[hostname].ip)
            return self.allocations[hostname].ip

        ip = requested_ip or self.get_next_available_ip()
        if not ip:
            logger.error("event=ip_allocation_failed hostname=%s reason=no_available_ips", hostname)
            return None

        if requested_ip and any(alloc.ip == requested_ip for alloc in self.allocations.values()):
            logger.error("event=ip_allocation_failed hostname=%s requested_ip=%s reason=ip_in_use", hostname, requested_ip)
            return None

        self.allocations[hostname] = IPAllocation(hostname=hostname, ip=ip)
        self.save_allocations()
        logger.debug("event=ip_allocated hostname=%s ip=%s", hostname, ip)
        return ip

    def deallocate_ip(self, hostname: str) -> bool:
        if hostname not in self.allocations:
            logger.debug("event=ip_not_allocated hostname=%s", hostname)
            return False

        ip = self.allocations[hostname].ip
        del self.allocations[hostname]
        self.save_allocations()
        logger.debug("event=ip_deallocated hostname=%s ip=%s", hostname, ip)
        return True

    def get_allocation(self, hostname: str) -> Optional[IPAllocation]:
        return self.allocations.get(hostname)

    def list_allocations(self) -> Dict[str, IPAllocation]:
        return self.allocations.copy()


def _prefix_from_netmask(netmask: str) -> int:
    try:
        if isinstance(netmask, int):
            return int(netmask)
        nm = str(netmask).strip()
        if nm.startswith("/"):
            nm = nm.lstrip("/")
        if nm.isdigit():
            return int(nm)
        return ipaddress.IPv4Network(f"0.0.0.0/{nm}").prefixlen
    except Exception:
        return 32


def check_ip_exists(interface: str, ip: str) -> bool:
    try:
        result = subprocess.run(
            ["ip", "addr", "show", interface],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            logger.debug("event=check_ip_failed_cmd interface=%s stderr=%s", interface, result.stderr.strip())
            return False

        pattern = re.compile(rf"\b{re.escape(ip)}\b")
        return bool(pattern.search(result.stdout))
    except Exception as e:
        logger.debug("event=check_ip_failed interface=%s ip=%s error=%s", interface, ip, str(e))
        return False


def _run_ip_command(args: List[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=5)
    except Exception as e:
        cp = subprocess.CompletedProcess(args=args, returncode=1, stdout="", stderr=str(e))
        return cp


def add_virtual_ip(interface: str, ip: str, netmask: str) -> bool:
    if check_ip_exists(interface, ip):
        logger.debug("event=virtual_ip_exists interface=%s ip=%s", interface, ip)
        return True

    prefix = _prefix_from_netmask(netmask)
    ip_with_prefix = f"{ip}/{prefix}"

    result = _run_ip_command(["ip", "addr", "add", ip_with_prefix, "dev", interface])
    if result.returncode == 0:
        logger.debug("event=virtual_ip_added interface=%s ip=%s", interface, ip)
        return True

    logger.error("event=virtual_ip_add_failed interface=%s ip=%s stderr=%s", interface, ip, result.stderr.strip())
    try:
        sudo_result = _run_ip_command(["sudo", "-n", "ip", "addr", "add", ip_with_prefix, "dev", interface])
        if sudo_result.returncode == 0:
            logger.debug("event=virtual_ip_added_sudo interface=%s ip=%s", interface, ip)
            return True
        logger.error("event=virtual_ip_add_failed_sudo interface=%s ip=%s stderr=%s", interface, ip, sudo_result.stderr.strip())
        return False
    except Exception as e:
        logger.error("event=virtual_ip_add_exception interface=%s ip=%s error=%s", interface, ip, str(e))
        return False


def remove_virtual_ip(interface: str, ip: str, netmask: str) -> bool:
    if not check_ip_exists(interface, ip):
        logger.debug("event=virtual_ip_not_exists interface=%s ip=%s", interface, ip)
        return True

    prefix = _prefix_from_netmask(netmask)
    ip_with_prefix = f"{ip}/{prefix}"

    result = _run_ip_command(["ip", "addr", "del", ip_with_prefix, "dev", interface])
    if result.returncode == 0:
        logger.debug("event=virtual_ip_removed interface=%s ip=%s", interface, ip)
        return True

    logger.error("event=virtual_ip_remove_failed interface=%s ip=%s stderr=%s", interface, ip, result.stderr.strip())
    try:
        sudo_result = _run_ip_command(["sudo", "-n", "ip", "addr", "del", ip_with_prefix, "dev", interface])
        if sudo_result.returncode == 0:
            logger.debug("event=virtual_ip_removed_sudo interface=%s ip=%s", interface, ip)
            return True
        logger.error("event=virtual_ip_remove_failed_sudo interface=%s ip=%s stderr=%s", interface, ip, sudo_result.stderr.strip())
        return False
    except Exception as e:
        logger.error("event=virtual_ip_remove_exception interface=%s ip=%s error=%s", interface, ip, str(e))
        return False


def verify_ip_connectivity(ip: str, hostname: str, extra_ips: Optional[List[str]] = None) -> bool:
    accepted_ips = {ip}
    if extra_ips:
        accepted_ips.update(str(candidate) for candidate in extra_ips if candidate)

    try:
        ai = socket.getaddrinfo(hostname, None)
        if not ai:
            return False
        for entry in ai:
            resolved_ip = entry[4][0]
            if resolved_ip in accepted_ips:
                return True
        return False
    except Exception as e:
        logger.debug(
            "event=verify_connectivity_failed ip=%s hostname=%s accepted=%s error=%s",
            ip,
            hostname,
            list(accepted_ips),
            str(e),
        )
        return False


def get_config_dir() -> Path:
    return Path(__file__).parent / "config"


@activity.defn(name="allocate_virtual_ips_activity")
async def allocate_virtual_ips_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    hostnames = params.get("hostnames", [])
    requested_ips = params.get("requested_ips", {})
    trace_id = params.get("trace_id", "vip-allocate")

    start_time = time.time()
    results = {}
    all_success = True

    logger.info("event=vip_allocate_start trace_id=%s hostnames_count=%d", trace_id, len(hostnames))

    config_dir = get_config_dir()
    config = VirtualIPConfig.from_yaml(config_dir)
    manager = VirtualIPManager(config, config_dir)

    for hostname in hostnames:
        requested_ip = requested_ips.get(hostname)
        logger.debug("event=vip_allocating trace_id=%s hostname=%s requested_ip=%s", trace_id, hostname, requested_ip)

        ip = manager.allocate_ip(hostname, requested_ip)
        if ip:
            ip_added = add_virtual_ip(config.interface, ip, config.netmask)
            if ip_added:
                alternate_ips = manager.get_expected_hostname_ips(hostname)
                connectivity_ok = verify_ip_connectivity(ip, hostname, alternate_ips)
                results[hostname] = {
                    "ip": ip,
                    "allocated": True,
                    "ip_added": True,
                    "connectivity_verified": connectivity_ok
                }
                logger.info("event=vip_allocated trace_id=%s hostname=%s ip=%s connectivity=%s",
                           trace_id, hostname, ip, connectivity_ok)
            else:
                all_success = False
                results[hostname] = {
                    "ip": ip,
                    "allocated": True,
                    "ip_added": False,
                    "error": "failed_to_add_ip"
                }
                logger.error("event=vip_allocate_failed trace_id=%s hostname=%s ip=%s reason=ip_add_failed",
                             trace_id, hostname, ip)
        else:
            all_success = False
            results[hostname] = {
                "allocated": False,
                "error": "allocation_failed"
            }
            logger.error("event=vip_allocate_failed trace_id=%s hostname=%s reason=allocation_failed",
                         trace_id, hostname)

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info("event=vip_allocate_complete trace_id=%s all_success=%s duration_ms=%d",
               trace_id, all_success, duration_ms)

    return {
        "success": all_success,
        "service": "virtual-ip-manager",
        "results": results,
        "duration_ms": duration_ms,
        "trace_id": trace_id
    }


@activity.defn(name="deallocate_virtual_ips_activity")
async def deallocate_virtual_ips_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    hostnames = params.get("hostnames", [])
    trace_id = params.get("trace_id", "vip-deallocate")
    remove_ip = params.get("remove_ip", True)

    start_time = time.time()
    results = {}
    all_success = True

    logger.info("event=vip_deallocate_start trace_id=%s hostnames_count=%d remove_ip=%s",
               trace_id, len(hostnames), remove_ip)

    config_dir = get_config_dir()
    config = VirtualIPConfig.from_yaml(config_dir)
    manager = VirtualIPManager(config, config_dir)

    for hostname in hostnames:
        logger.debug("event=vip_deallocating trace_id=%s hostname=%s", trace_id, hostname)

        allocation = manager.get_allocation(hostname)
        if not allocation:
            results[hostname] = {
                "deallocated": False,
                "reason": "not_allocated"
            }
            logger.debug("event=vip_not_allocated trace_id=%s hostname=%s", trace_id, hostname)
            continue

        ip = allocation.ip
        ip_removed = True

        if remove_ip:
            ip_removed = remove_virtual_ip(config.interface, ip, config.netmask)

        deallocated = manager.deallocate_ip(hostname)

        if deallocated and ip_removed:
            results[hostname] = {
                "ip": ip,
                "deallocated": True,
                "ip_removed": remove_ip
            }
            logger.info("event=vip_deallocated trace_id=%s hostname=%s ip=%s ip_removed=%s",
                       trace_id, hostname, ip, remove_ip)
        else:
            all_success = False
            results[hostname] = {
                "ip": ip,
                "deallocated": deallocated,
                "ip_removed": ip_removed,
                "error": "deallocation_failed"
            }
            logger.error("event=vip_deallocate_failed trace_id=%s hostname=%s ip=%s",
                         trace_id, hostname, ip)

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info("event=vip_deallocate_complete trace_id=%s all_success=%s duration_ms=%d",
               trace_id, all_success, duration_ms)

    return {
        "success": all_success,
        "service": "virtual-ip-manager",
        "results": results,
        "duration_ms": duration_ms,
        "trace_id": trace_id
    }


@activity.defn(name="list_virtual_ip_allocations_activity")
async def list_virtual_ip_allocations_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    trace_id = params.get("trace_id", "vip-list")

    start_time = time.time()

    logger.info("event=vip_list_start trace_id=%s", trace_id)

    config_dir = get_config_dir()
    config = VirtualIPConfig.from_yaml(config_dir)
    manager = VirtualIPManager(config, config_dir)

    allocations = manager.list_allocations()

    results = {
        hostname: {
            "ip": alloc.ip,
            "allocated_at": alloc.allocated_at,
            "ip_exists": check_ip_exists(config.interface, alloc.ip)
        }
        for hostname, alloc in allocations.items()
    }

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info("event=vip_list_complete trace_id=%s allocations_count=%d duration_ms=%d",
               trace_id, len(results), duration_ms)

    return {
        "success": True,
        "service": "virtual-ip-manager",
        "allocations": results,
        "total_count": len(results),
        "duration_ms": duration_ms,
        "trace_id": trace_id
    }


@activity.defn(name="verify_virtual_ips_activity")
async def verify_virtual_ips_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    hostnames = params.get("hostnames", [])
    trace_id = params.get("trace_id", "vip-verify")

    start_time = time.time()
    results = {}
    all_verified = True

    logger.info("event=vip_verify_start trace_id=%s hostnames_count=%d", trace_id, len(hostnames))

    config_dir = get_config_dir()
    config = VirtualIPConfig.from_yaml(config_dir)
    manager = VirtualIPManager(config, config_dir)

    for hostname in hostnames:
        logger.debug("event=vip_verifying trace_id=%s hostname=%s", trace_id, hostname)

        allocation = manager.get_allocation(hostname)
        if not allocation:
            results[hostname] = {
                "allocated": False,
                "ip_exists": False,
                "connectivity_verified": False,
                "verified": False
            }
            all_verified = False
            logger.warning("event=vip_verify_failed trace_id=%s hostname=%s reason=not_allocated",
                          trace_id, hostname)
            continue

        ip = allocation.ip
        ip_exists = check_ip_exists(config.interface, ip)
        alternate_ips = manager.get_expected_hostname_ips(hostname)
        connectivity_ok = verify_ip_connectivity(ip, hostname, alternate_ips) if ip_exists else False
        verified = ip_exists and connectivity_ok

        results[hostname] = {
            "ip": ip,
            "allocated": True,
            "ip_exists": ip_exists,
            "connectivity_verified": connectivity_ok,
            "verified": verified
        }

        if not verified:
            all_verified = False
            logger.warning("event=vip_verify_failed trace_id=%s hostname=%s ip=%s ip_exists=%s connectivity=%s",
                          trace_id, hostname, ip, ip_exists, connectivity_ok)
        else:
            logger.info("event=vip_verified trace_id=%s hostname=%s ip=%s", trace_id, hostname, ip)

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info("event=vip_verify_complete trace_id=%s all_verified=%s duration_ms=%d",
               trace_id, all_verified, duration_ms)

    return {
        "success": all_verified,
        "service": "virtual-ip-manager",
        "results": results,
        "duration_ms": duration_ms,
        "trace_id": trace_id
    }