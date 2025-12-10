# infrastructure/orchestrator/config/docker/traefik/host_manage_activity.py
from pathlib import Path
from typing import Dict, Any, Optional, List
from temporalio import activity
import logging
import os
import re
import socket
import subprocess
import tempfile
import time

logger = logging.getLogger(__name__)

DEFAULT_HOSTS_FILE = Path(os.environ.get("HOSTS_FILE", "/etc/hosts"))

DEFAULT_BACKUP_DIR = Path(os.environ.get("HOSTS_BACKUP_DIR", str(Path.home() / ".hosts_backups")))


def _now_ts() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def _ensure_backup_dir(path: Path) -> Path:
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except Exception:
        fallback = Path.home() / ".hosts_backups"
        try:
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback
        except Exception:
            return Path("/tmp")


def _backup_hosts_file(hosts_file: Path, backup_dir: Path) -> Optional[str]:
    backup_dir = _ensure_backup_dir(backup_dir)
    timestamp = _now_ts()
    backup_path = backup_dir / f"hosts.backup.{timestamp}"
    try:
        if os.access(hosts_file, os.R_OK):
            with hosts_file.open("rb") as src, backup_path.open("wb") as dst:
                dst.write(src.read())
            return str(backup_path)
        else:
            proc = subprocess.run(["sudo", "-n", "cp", str(hosts_file), str(backup_path)],
                                  check=False, capture_output=True)
            if proc.returncode == 0:
                return str(backup_path)
            logger.error("event=hosts_backup_failed sudo_copy stderr=%s", proc.stderr.decode().strip())
            return None
    except Exception as e:
        logger.error("event=hosts_backup_failed error=%s", str(e))
        return None

def _read_hosts(hosts_file: Path) -> str:
    try:
        with hosts_file.open("r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        proc = subprocess.run(["sudo", "-n", "cat", str(hosts_file)], check=False, capture_output=True)
        if proc.returncode == 0:
            return proc.stdout.decode("utf-8")
        return ""

def _atomic_write(hosts_file: Path, content: str) -> bool:
    tmp_dir = Path(tempfile.gettempdir())
    fd, tmp_path = tempfile.mkstemp(dir=str(tmp_dir))
    os.close(fd)
    tmp_path = str(tmp_path)
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
        try:
            os.replace(tmp_path, str(hosts_file))
            return True
        except PermissionError:
            proc = subprocess.run(["sudo", "-n", "cp", tmp_path, str(hosts_file)], check=False, capture_output=True)
            if proc.returncode == 0:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                return True
            logger.error("event=hosts_atomic_write_failed sudo_cp_stderr=%s", proc.stderr.decode().strip())
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            return False
        except Exception as e:
            logger.error("event=hosts_atomic_write_failed error=%s", str(e))
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            return False
    except Exception as e:
        logger.error("event=hosts_atomic_write_failed error=%s", str(e))
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        return False

def _remove_hostname_lines(content: str, hostname: str) -> str:
    pattern = re.compile(rf"^\s*\S+\s+{re.escape(hostname)}(\s.*)?$", flags=re.MULTILINE)
    return pattern.sub("", content)

def _normalize_entry(ip: str, hostname: str) -> str:
    return f"{ip} {hostname}"

def _resolve_host(hostname: str, expected_ip: Optional[str] = None, timeout_sec: float = 2.0) -> bool:
    try:
        ai = socket.getaddrinfo(hostname, None)
        if not ai:
            return False
        if expected_ip:
            for entry in ai:
                addr = entry[4][0]
                if addr == expected_ip:
                    return True
            return False
        return True
    except Exception:
        return False

@activity.defn(name="add_hosts_entries_activity")
async def add_hosts_entries_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    entries: List[Dict[str, str]] = params.get("entries", [])
    trace_id = params.get("trace_id", "hosts-add")
    force_replace = params.get("force_replace", True)
    hosts_file = Path(params.get("hosts_file", str(DEFAULT_HOSTS_FILE)))
    backup_dir = Path(params.get("backup_dir", str(DEFAULT_BACKUP_DIR)))

    start_time = time.time()
    results: Dict[str, Any] = {}
    all_success = True

    logger.info("event=hosts_add_start trace_id=%s entries_count=%d force_replace=%s", trace_id, len(entries), force_replace)

    backup_path = _backup_hosts_file(hosts_file, backup_dir)
    if not backup_path:
        logger.warning("event=hosts_backup_skipped trace_id=%s", trace_id)
    else:
        logger.info("event=hosts_backup_created trace_id=%s backup_path=%s", trace_id, backup_path)

    current = _read_hosts(hosts_file)

    for entry in entries:
        ip = entry.get("ip", "127.0.0.1")
        hostname = entry.get("hostname")
        if not hostname:
            logger.warning("event=hosts_entry_skipped trace_id=%s reason=missing_hostname", trace_id)
            continue

        logger.info("event=hosts_entry_processing trace_id=%s ip=%s hostname=%s", trace_id, ip, hostname)

        exists = bool(re.search(rf"^\s*\S+\s+{re.escape(hostname)}(\s.*)?$", current, flags=re.MULTILINE))

        if exists and not force_replace:
            results[hostname] = {"ip": ip, "added": False, "skipped": True, "reason": "already_exists"}
            logger.info("event=hosts_entry_exists_skipped trace_id=%s hostname=%s", trace_id, hostname)
            continue

        if exists and force_replace:
            current = _remove_hostname_lines(current, hostname)
            logger.info("event=hosts_entry_exists_replacing trace_id=%s hostname=%s", trace_id, hostname)

        entry_line = _normalize_entry(ip, hostname)
        if not current.endswith("\n"):
            current = current + "\n"
        current = current + entry_line + "\n"

        written = _atomic_write(hosts_file, current)

        if written:
            dns_ok = _resolve_host(hostname, expected_ip=ip)
            results[hostname] = {"ip": ip, "added": True, "dns_verified": dns_ok}
            logger.info("event=hosts_entry_added trace_id=%s ip=%s hostname=%s dns_verified=%s", trace_id, ip, hostname, dns_ok)
        else:
            all_success = False
            results[hostname] = {"ip": ip, "added": False, "error": "failed_to_add"}
            logger.error("event=hosts_entry_add_failed trace_id=%s ip=%s hostname=%s", trace_id, ip, hostname)

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info("event=hosts_add_complete trace_id=%s all_success=%s duration_ms=%d", trace_id, all_success, duration_ms)

    return {
        "success": all_success,
        "service": "hosts-manager",
        "results": results,
        "backup_path": backup_path,
        "duration_ms": duration_ms,
        "trace_id": trace_id
    }

@activity.defn(name="remove_hosts_entries_activity")
async def remove_hosts_entries_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    hostnames: List[str] = params.get("hostnames", [])
    trace_id = params.get("trace_id", "hosts-remove")
    hosts_file = Path(params.get("hosts_file", str(DEFAULT_HOSTS_FILE)))
    backup_dir = Path(params.get("backup_dir", str(DEFAULT_BACKUP_DIR)))

    start_time = time.time()
    results: Dict[str, Any] = {}
    all_success = True

    logger.info("event=hosts_remove_start trace_id=%s hostnames_count=%d", trace_id, len(hostnames))

    backup_path = _backup_hosts_file(hosts_file, backup_dir)
    if backup_path:
        logger.info("event=hosts_backup_created trace_id=%s backup_path=%s", trace_id, backup_path)
    else:
        logger.warning("event=hosts_backup_skipped trace_id=%s", trace_id)

    current = _read_hosts(hosts_file)

    for hostname in hostnames:
        logger.info("event=hosts_entry_removing trace_id=%s hostname=%s", trace_id, hostname)
        exists = bool(re.search(rf"^\s*\S+\s+{re.escape(hostname)}(\s.*)?$", current, flags=re.MULTILINE))
        if not exists:
            results[hostname] = {"removed": False, "reason": "not_found"}
            logger.info("event=hosts_entry_not_found trace_id=%s hostname=%s", trace_id, hostname)
            continue

        new_content = _remove_hostname_lines(current, hostname)
        if not new_content.endswith("\n"):
            new_content = new_content + "\n"

        written = _atomic_write(hosts_file, new_content)

        if written:
            results[hostname] = {"removed": True}
            current = new_content
            logger.info("event=hosts_entry_removed trace_id=%s hostname=%s", trace_id, hostname)
        else:
            all_success = False
            results[hostname] = {"removed": False, "error": "failed_to_remove"}
            logger.error("event=hosts_entry_remove_failed trace_id=%s hostname=%s", trace_id, hostname)

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info("event=hosts_remove_complete trace_id=%s all_success=%s duration_ms=%d", trace_id, all_success, duration_ms)

    return {
        "success": all_success,
        "service": "hosts-manager",
        "results": results,
        "backup_path": backup_path,
        "duration_ms": duration_ms,
        "trace_id": trace_id
    }

@activity.defn(name="verify_hosts_entries_activity")
async def verify_hosts_entries_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    hostnames: List[str] = params.get("hostnames", [])
    trace_id = params.get("trace_id", "hosts-verify")
    hosts_file = Path(params.get("hosts_file", str(DEFAULT_HOSTS_FILE)))

    start_time = time.time()
    results: Dict[str, Any] = {}
    all_verified = True

    logger.info("event=hosts_verify_start trace_id=%s hostnames_count=%d", trace_id, len(hostnames))

    for hostname in hostnames:
        logger.info("event=hosts_entry_verifying trace_id=%s hostname=%s", trace_id, hostname)
        exists = bool(re.search(rf"^\s*\S+\s+{re.escape(hostname)}(\s.*)?$", _read_hosts(hosts_file), flags=re.MULTILINE))
        dns_ok = _resolve_host(hostname) if exists else False
        results[hostname] = {"exists": exists, "dns_verified": dns_ok, "verified": exists and dns_ok}
        if not (exists and dns_ok):
            all_verified = False
            logger.warning("event=hosts_entry_verify_failed trace_id=%s hostname=%s exists=%s dns_ok=%s", trace_id, hostname, exists, dns_ok)
        else:
            logger.info("event=hosts_entry_verified trace_id=%s hostname=%s", trace_id, hostname)

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info("event=hosts_verify_complete trace_id=%s all_verified=%s duration_ms=%d", trace_id, all_verified, duration_ms)

    return {
        "success": all_verified,
        "service": "hosts-manager",
        "results": results,
        "duration_ms": duration_ms,
        "trace_id": trace_id
    }

@activity.defn(name="restore_hosts_backup_activity")
async def restore_hosts_backup_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    backup_path = params.get("backup_path")
    trace_id = params.get("trace_id", "hosts-restore")
    hosts_file = Path(params.get("hosts_file", str(DEFAULT_HOSTS_FILE)))

    start_time = time.time()
    logger.info("event=hosts_restore_start trace_id=%s backup_path=%s", trace_id, backup_path)

    if not backup_path or not Path(backup_path).exists():
        logger.error("event=hosts_restore_failed trace_id=%s reason=backup_not_found backup_path=%s", trace_id, backup_path)
        return {"success": False, "service": "hosts-manager", "error": "backup_not_found", "trace_id": trace_id}

    try:
        if os.access(hosts_file, os.W_OK):
            with Path(backup_path).open("rb") as src, hosts_file.open("wb") as dst:
                dst.write(src.read())
            duration_ms = int((time.time() - start_time) * 1000)
            logger.info("event=hosts_restore_complete trace_id=%s backup_path=%s duration_ms=%d", trace_id, backup_path, duration_ms)
            return {"success": True, "service": "hosts-manager", "backup_path": backup_path, "duration_ms": duration_ms, "trace_id": trace_id}
        else:
            proc = subprocess.run(["sudo", "-n", "cp", str(backup_path), str(hosts_file)], check=False, capture_output=True)
            if proc.returncode == 0:
                duration_ms = int((time.time() - start_time) * 1000)
                logger.info("event=hosts_restore_complete trace_id=%s backup_path=%s duration_ms=%d", trace_id, backup_path, duration_ms)
                return {"success": True, "service": "hosts-manager", "backup_path": backup_path, "duration_ms": duration_ms, "trace_id": trace_id}
            logger.error("event=hosts_restore_failed stderr=%s", proc.stderr.decode().strip())
            return {"success": False, "service": "hosts-manager", "error": "restore_failed", "trace_id": trace_id}
    except Exception as e:
        logger.error("event=hosts_restore_failed error=%s", str(e))
        return {"success": False, "service": "hosts-manager", "error": str(e), "trace_id": trace_id}
