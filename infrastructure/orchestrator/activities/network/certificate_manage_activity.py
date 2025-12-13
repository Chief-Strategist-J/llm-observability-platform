from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from temporalio import activity
import logging
import subprocess
import time
import yaml

logger = logging.getLogger(__name__)


@dataclass
class CertificateConfig:
    certs_dir: Path = field(default_factory=lambda: Path.home() / ".certs")
    validity_days: int = 365
    key_size: int = 4096

    @classmethod
    def from_yaml(cls, config_dir: Path) -> "CertificateConfig":
        config_path = config_dir / "certificate_config.yaml"
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    data = yaml.safe_load(f) or {}
                certs_dir = data.get("certs_dir")
                if certs_dir:
                    data["certs_dir"] = Path(certs_dir)
                return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
            except Exception as e:
                logger.warning("event=config_load_failed path=%s error=%s", config_path, str(e))
        return cls()

    def save(self, config_dir: Path):
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            config_path = config_dir / "certificate_config.yaml"
            data = asdict(self)
            data["certs_dir"] = str(data["certs_dir"])
            with open(config_path, "w") as f:
                yaml.dump(data, f, default_flow_style=False)
            logger.debug("event=config_saved path=%s", config_path)
        except Exception as e:
            logger.warning("event=config_save_failed error=%s", str(e))


@dataclass
class CertificateInfo:
    hostname: str
    cert_file: str
    key_file: str
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CertificateManager:
    def __init__(self, config: CertificateConfig, config_dir: Path):
        self.config = config
        self.config_dir = config_dir
        self.certificates_file = config_dir / "certificate_registry.yaml"
        self.certificates: Dict[str, CertificateInfo] = self.load_certificates()

    def load_certificates(self) -> Dict[str, CertificateInfo]:
        if not self.certificates_file.exists():
            return {}
        try:
            with open(self.certificates_file, "r") as f:
                data = yaml.safe_load(f) or {}
            return {k: CertificateInfo(**v) for k, v in data.items()}
        except Exception as e:
            logger.warning("event=certificates_load_failed path=%s error=%s", self.certificates_file, str(e))
            return {}

    def save_certificates(self):
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.certificates_file, "w") as f:
                yaml.dump({k: v.to_dict() for k, v in self.certificates.items()}, f, default_flow_style=False)
        except Exception as e:
            logger.warning("event=certificates_save_failed path=%s error=%s", self.certificates_file, str(e))

    def get_certificate(self, hostname: str) -> Optional[CertificateInfo]:
        return self.certificates.get(hostname)

    def register_certificate(self, hostname: str, cert_file: str, key_file: str) -> CertificateInfo:
        cert_info = CertificateInfo(hostname=hostname, cert_file=cert_file, key_file=key_file)
        self.certificates[hostname] = cert_info
        self.save_certificates()
        return cert_info

    def unregister_certificate(self, hostname: str) -> bool:
        if hostname not in self.certificates:
            return False
        del self.certificates[hostname]
        self.save_certificates()
        return True

    def list_certificates(self) -> Dict[str, CertificateInfo]:
        return self.certificates.copy()


def run_command(cmd: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        return subprocess.CompletedProcess(cmd, 1, "", f"Command timed out: {e}")
    except Exception as e:
        return subprocess.CompletedProcess(cmd, 1, "", str(e))


def check_mkcert_available() -> bool:
    result = run_command(["which", "mkcert"])
    return result.returncode == 0


def generate_certificate_mkcert(hostname: str, cert_file: Path, key_file: Path) -> bool:
    cmd = ["mkcert", "-cert-file", str(cert_file), "-key-file", str(key_file), hostname, f"*.{hostname}"]
    result = run_command(cmd)
    return result.returncode == 0


def generate_certificate_openssl(hostname: str, cert_file: Path, key_file: Path, validity_days: int = 365, key_size: int = 4096) -> bool:
    cmd = [
        "openssl", "req", "-x509", "-newkey", f"rsa:{key_size}",
        "-keyout", str(key_file),
        "-out", str(cert_file),
        "-days", str(validity_days),
        "-nodes",
        "-subj", f"/CN={hostname}",
        "-addext", f"subjectAltName=DNS:{hostname},DNS:*.{hostname}"
    ]
    result = run_command(cmd)
    return result.returncode == 0


def verify_certificate(cert_file: Path) -> bool:
    if not cert_file.exists():
        return False
    cmd = ["openssl", "x509", "-noout", "-text", "-in", str(cert_file)]
    result = run_command(cmd)
    return result.returncode == 0


def get_config_dir() -> Path:
    return Path(__file__).parent / "config"


@activity.defn(name="generate_certificates_activity")
async def generate_certificates_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    hostnames = params.get("hostnames", [])
    certs_dir = Path(params.get("certs_dir", str(Path.home() / ".certs")))
    trace_id = params.get("trace_id", "cert-gen")
    use_mkcert = params.get("use_mkcert", True)
    validity_days = params.get("validity_days", 365)
    key_size = params.get("key_size", 4096)

    start_time = time.time()
    results = {}
    all_success = True

    logger.info("event=generate_certificates_start trace_id=%s hostnames_count=%d certs_dir=%s", 
                trace_id, len(hostnames), str(certs_dir))

    try:
        certs_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error("event=certs_dir_create_failed trace_id=%s error=%s", trace_id, str(e))
        return {
            "success": False,
            "service": "certificate-manager",
            "error": str(e),
            "trace_id": trace_id
        }

    config_dir = get_config_dir()
    config = CertificateConfig(certs_dir=certs_dir, validity_days=validity_days, key_size=key_size)
    manager = CertificateManager(config, config_dir)

    mkcert_available = check_mkcert_available() if use_mkcert else False

    for hostname in hostnames:
        logger.info("event=generating_certificate trace_id=%s hostname=%s", trace_id, hostname)

        cert_file = certs_dir / f"{hostname}.pem"
        key_file = certs_dir / f"{hostname}-key.pem"

        if cert_file.exists() and key_file.exists():
            results[hostname] = {
                "generated": False,
                "exists": True,
                "cert_file": str(cert_file),
                "key_file": str(key_file)
            }
            logger.info("event=certificate_exists trace_id=%s hostname=%s", trace_id, hostname)
            continue

        if mkcert_available:
            success = generate_certificate_mkcert(hostname, cert_file, key_file)
        else:
            success = generate_certificate_openssl(hostname, cert_file, key_file, validity_days, key_size)

        if success and cert_file.exists() and key_file.exists():
            manager.register_certificate(hostname, str(cert_file), str(key_file))
            results[hostname] = {
                "generated": True,
                "cert_file": str(cert_file),
                "key_file": str(key_file),
                "method": "mkcert" if mkcert_available else "openssl"
            }
            logger.info("event=certificate_generated trace_id=%s hostname=%s method=%s", 
                       trace_id, hostname, "mkcert" if mkcert_available else "openssl")
        else:
            all_success = False
            results[hostname] = {
                "generated": False,
                "error": "generation_failed"
            }
            logger.error("event=certificate_generation_failed trace_id=%s hostname=%s", trace_id, hostname)

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info("event=generate_certificates_complete trace_id=%s all_success=%s duration_ms=%d", 
               trace_id, all_success, duration_ms)

    return {
        "success": all_success,
        "service": "certificate-manager",
        "results": results,
        "duration_ms": duration_ms,
        "trace_id": trace_id
    }


@activity.defn(name="delete_certificates_activity")
async def delete_certificates_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    hostnames = params.get("hostnames", [])
    certs_dir = Path(params.get("certs_dir", str(Path.home() / ".certs")))
    trace_id = params.get("trace_id", "cert-delete")

    start_time = time.time()
    results = {}
    all_success = True

    logger.info("event=delete_certificates_start trace_id=%s hostnames_count=%d", trace_id, len(hostnames))

    config_dir = get_config_dir()
    config = CertificateConfig(certs_dir=certs_dir)
    manager = CertificateManager(config, config_dir)

    for hostname in hostnames:
        logger.info("event=deleting_certificate trace_id=%s hostname=%s", trace_id, hostname)

        cert_file = certs_dir / f"{hostname}.pem"
        key_file = certs_dir / f"{hostname}-key.pem"

        files_deleted = []
        try:
            if cert_file.exists():
                cert_file.unlink()
                files_deleted.append(str(cert_file))
            if key_file.exists():
                key_file.unlink()
                files_deleted.append(str(key_file))

            manager.unregister_certificate(hostname)

            results[hostname] = {
                "deleted": True,
                "files_deleted": files_deleted
            }
            logger.info("event=certificate_deleted trace_id=%s hostname=%s files=%s", 
                       trace_id, hostname, files_deleted)
        except Exception as e:
            all_success = False
            results[hostname] = {
                "deleted": False,
                "error": str(e)
            }
            logger.error("event=certificate_delete_failed trace_id=%s hostname=%s error=%s", 
                        trace_id, hostname, str(e))

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info("event=delete_certificates_complete trace_id=%s all_success=%s duration_ms=%d", 
               trace_id, all_success, duration_ms)

    return {
        "success": all_success,
        "service": "certificate-manager",
        "results": results,
        "duration_ms": duration_ms,
        "trace_id": trace_id
    }


@activity.defn(name="verify_certificates_activity")
async def verify_certificates_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    hostnames = params.get("hostnames", [])
    certs_dir = Path(params.get("certs_dir", str(Path.home() / ".certs")))
    trace_id = params.get("trace_id", "cert-verify")

    start_time = time.time()
    results = {}
    all_verified = True

    logger.info("event=verify_certificates_start trace_id=%s hostnames_count=%d", trace_id, len(hostnames))

    for hostname in hostnames:
        logger.info("event=verifying_certificate trace_id=%s hostname=%s", trace_id, hostname)

        cert_file = certs_dir / f"{hostname}.pem"
        key_file = certs_dir / f"{hostname}-key.pem"

        cert_exists = cert_file.exists()
        key_exists = key_file.exists()
        cert_valid = verify_certificate(cert_file) if cert_exists else False

        verified = cert_exists and key_exists and cert_valid

        results[hostname] = {
            "cert_exists": cert_exists,
            "key_exists": key_exists,
            "cert_valid": cert_valid,
            "verified": verified,
            "cert_file": str(cert_file) if cert_exists else None,
            "key_file": str(key_file) if key_exists else None
        }

        if not verified:
            all_verified = False
            logger.warning("event=certificate_verify_failed trace_id=%s hostname=%s cert_exists=%s key_exists=%s cert_valid=%s", 
                          trace_id, hostname, cert_exists, key_exists, cert_valid)
        else:
            logger.info("event=certificate_verified trace_id=%s hostname=%s", trace_id, hostname)

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info("event=verify_certificates_complete trace_id=%s all_verified=%s duration_ms=%d", 
               trace_id, all_verified, duration_ms)

    return {
        "success": all_verified,
        "service": "certificate-manager",
        "results": results,
        "duration_ms": duration_ms,
        "trace_id": trace_id
    }


@activity.defn(name="list_certificates_activity")
async def list_certificates_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    certs_dir = Path(params.get("certs_dir", str(Path.home() / ".certs")))
    trace_id = params.get("trace_id", "cert-list")

    start_time = time.time()

    logger.info("event=list_certificates_start trace_id=%s certs_dir=%s", trace_id, str(certs_dir))

    config_dir = get_config_dir()
    config = CertificateConfig(certs_dir=certs_dir)
    manager = CertificateManager(config, config_dir)

    certificates = manager.list_certificates()

    results = {}
    for hostname, cert_info in certificates.items():
        cert_file = Path(cert_info.cert_file)
        key_file = Path(cert_info.key_file)
        results[hostname] = {
            "cert_file": cert_info.cert_file,
            "key_file": cert_info.key_file,
            "created_at": cert_info.created_at,
            "cert_exists": cert_file.exists(),
            "key_exists": key_file.exists()
        }

    duration_ms = int((time.time() - start_time) * 1000)
    logger.info("event=list_certificates_complete trace_id=%s count=%d duration_ms=%d", 
               trace_id, len(results), duration_ms)

    return {
        "success": True,
        "service": "certificate-manager",
        "certificates": results,
        "total_count": len(results),
        "certs_dir": str(certs_dir),
        "duration_ms": duration_ms,
        "trace_id": trace_id
    }


@activity.defn(name="generate_traefik_tls_config_activity")
async def generate_traefik_tls_config_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    hostnames = params.get("hostnames", [])
    certs_dir = params.get("certs_dir", "/certs")
    output_file = Path(params.get("output_file", "./traefik_dynamic_tls.yaml"))
    trace_id = params.get("trace_id", "traefik-tls-config")

    start_time = time.time()

    logger.info("event=generate_traefik_tls_config_start trace_id=%s hostnames_count=%d output_file=%s", 
               trace_id, len(hostnames), str(output_file))

    try:
        certificates = []
        for hostname in hostnames:
            cert_file = f"{certs_dir}/{hostname}.pem"
            key_file = f"{certs_dir}/{hostname}-key.pem"
            certificates.append({
                "certFile": cert_file,
                "keyFile": key_file
            })

        config = {
            "tls": {
                "certificates": certificates,
                "stores": {
                    "default": {
                        "defaultCertificate": {
                            "certFile": certificates[0]["certFile"],
                            "keyFile": certificates[0]["keyFile"]
                        }
                    }
                } if certificates else {}
            }
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        duration_ms = int((time.time() - start_time) * 1000)
        logger.info("event=generate_traefik_tls_config_complete trace_id=%s output_file=%s certificates_count=%d duration_ms=%d", 
                   trace_id, str(output_file), len(certificates), duration_ms)

        return {
            "success": True,
            "service": "certificate-manager",
            "output_file": str(output_file),
            "certificates_count": len(certificates),
            "duration_ms": duration_ms,
            "trace_id": trace_id
        }
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error("event=generate_traefik_tls_config_failed trace_id=%s error=%s", trace_id, str(e))
        return {
            "success": False,
            "service": "certificate-manager",
            "error": str(e),
            "duration_ms": duration_ms,
            "trace_id": trace_id
        }
