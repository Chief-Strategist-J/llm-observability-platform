from __future__ import annotations

import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Any

import yaml
from temporalio import activity

logger = logging.getLogger(__name__)


def run_command(command: List[str], timeout: int = 300) -> Dict[str, Any]:
    logger.info("event=command_execute command=%s", " ".join(command))
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        success = result.returncode == 0
        logger.info("event=command_result success=%s returncode=%d", success, result.returncode)
        if not success:
            logger.error("event=command_failed stderr=%s", result.stderr[:500])
        return {
            "success": success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        logger.error("event=command_timeout timeout=%d", timeout)
        return {"success": False, "stdout": "", "stderr": f"Timeout after {timeout}s", "returncode": -1}
    except Exception as e:
        logger.error("event=command_exception error=%s", str(e))
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


@activity.defn(name="create_root_ca_activity")
async def create_root_ca_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        certs_dir: str = params.get("certs_dir", "infrastructure/orchestrator/config/docker/traefik/certs")
        logger.info("event=create_root_ca_start certs_dir=%s", certs_dir)
        ca_key_path = Path(certs_dir) / "rootCA.key"
        ca_cert_path = Path(certs_dir) / "rootCA.pem"
        
        if ca_key_path.exists() and ca_cert_path.exists():
            logger.info("event=root_ca_exists cert=%s", str(ca_cert_path))
            return {"success": True, "created": False, "ca_cert_path": str(ca_cert_path), "ca_key_path": str(ca_key_path)}

        # Generate Private Key
        run_command(["openssl", "genrsa", "-out", str(ca_key_path), "4096"])
        
        # Generate Root Certificate
        result = run_command([
            "openssl", "req", "-x509", "-new", "-nodes", "-days", "3650",
            "-key", str(ca_key_path),
            "-sha256", "-out", str(ca_cert_path),
            "-subj", "/C=US/ST=State/L=City/O=ScaibuLocal/CN=ScaibuLocalRootCA"
        ])
        
        if result["success"]:
            logger.info("event=create_root_ca_complete cert=%s", str(ca_cert_path))
            return {"success": True, "created": True, "ca_cert_path": str(ca_cert_path), "ca_key_path": str(ca_key_path)}
        else:
            logger.error("event=create_root_ca_failed stderr=%s", result["stderr"])
            return {"success": False, "error": result["stderr"]}
    except Exception as e:
        logger.error("event=create_root_ca_exception error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="install_root_ca_activity")
async def install_root_ca_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        certs_dir: str = params.get("certs_dir", "infrastructure/orchestrator/config/docker/traefik/certs")
        ca_cert_path = Path(certs_dir) / "rootCA.pem"
        
        if not ca_cert_path.exists():
             return {"success": False, "error": "Root CA not found"}

        logger.info("event=install_root_ca_start cert=%s", str(ca_cert_path))
        
        # Check if sudo is non-interactive
        sudo_check = run_command(["sudo", "-n", "true"])
        if not sudo_check["success"]:
            logger.warning("event=install_root_ca_skipped reason=sudo_requires_password hint='Run manually: sudo cp %s /usr/local/share/ca-certificates/scaibu-root-ca.crt && sudo update-ca-certificates'", str(ca_cert_path))
            return {"success": True, "installed": False, "reason": "sudo_requires_password"}

        # 1. Copy to ca-certificates dir
        target_path = "/usr/local/share/ca-certificates/scaibu-root-ca.crt"
        copy_result = run_command(["sudo", "-n", "cp", str(ca_cert_path), target_path])
        if not copy_result["success"]:
             return {"success": False, "error": f"Failed to copy CA: {copy_result['stderr']}"}

        # 2. Update certificates
        update_result = run_command(["sudo", "-n", "update-ca-certificates"])
        if not update_result["success"]:
             return {"success": False, "error": f"Failed to update CA certificates: {update_result['stderr']}"}

        logger.info("event=install_root_ca_complete")
        return {"success": True, "installed": True}
    except Exception as e:
        logger.error("event=install_root_ca_exception error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="create_tls_directories_activity")
async def create_tls_directories_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        tls_config_dir: str = params.get("tls_config_dir", "infrastructure/orchestrator/config/docker/traefik/config/tls")
        certs_dir: str = params.get("certs_dir", "infrastructure/orchestrator/config/docker/traefik/certs")
        logger.info("event=create_tls_directories_start tls_config_dir=%s certs_dir=%s", tls_config_dir, certs_dir)
        Path(tls_config_dir).mkdir(parents=True, exist_ok=True)
        Path(certs_dir).mkdir(parents=True, exist_ok=True)
        return {"success": True, "tls_config_dir": tls_config_dir, "certs_dir": certs_dir}
    except Exception as e:
        logger.error("event=create_tls_directories_failed error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="generate_certificate_activity")
async def generate_certificate_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        hostname: str = params["hostname"]
        certs_dir: str = params.get("certs_dir", "infrastructure/orchestrator/config/docker/traefik/certs")
        logger.info("event=generate_certificate_start hostname=%s certs_dir=%s", hostname, certs_dir)
        
        cert_path = Path(certs_dir) / f"{hostname}.pem"
        key_path = Path(certs_dir) / f"{hostname}-key.pem"
        csr_path = Path(certs_dir) / f"{hostname}.csr"
        ext_path = Path(certs_dir) / f"{hostname}.ext"
        
        ca_key_path = Path(certs_dir) / "rootCA.key"
        ca_cert_path = Path(certs_dir) / "rootCA.pem"

        
        for p in [cert_path, key_path, csr_path, ext_path]:
            if p.exists(): p.unlink()

        
        run_command(["openssl", "genrsa", "-out", str(key_path), "4096"])

        
        run_command([
            "openssl", "req", "-new", "-key", str(key_path), "-out", str(csr_path),
            "-subj", f"/CN={hostname}"
        ])

        
        with open(ext_path, "w") as f:
            f.write(f"authorityKeyIdentifier=keyid,issuer\n")
            f.write(f"basicConstraints=CA:FALSE\n")
            f.write(f"keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment\n")
            f.write(f"subjectAltName = @alt_names\n\n")
            f.write(f"[alt_names]\n")
            f.write(f"DNS.1 = {hostname}\n")
            f.write(f"DNS.2 = *.{hostname}\n")


        result = run_command([
            "openssl", "x509", "-req", "-in", str(csr_path),
            "-CA", str(ca_cert_path), "-CAkey", str(ca_key_path),
            "-CAcreateserial", "-out", str(cert_path),
            "-days", "365", "-sha256", "-extfile", str(ext_path)
        ])

        if csr_path.exists(): csr_path.unlink()
        if ext_path.exists(): ext_path.unlink()

        if result["success"]:
            logger.info("event=generate_certificate_complete hostname=%s cert=%s", hostname, str(cert_path))
        else:
            logger.error("event=generate_certificate_failed hostname=%s stderr=%s", hostname, result["stderr"])
        
        return {
            "success": result["success"],
            "hostname": hostname,
            "cert_path": str(cert_path),
            "key_path": str(key_path)
        }
    except Exception as e:
        logger.error("event=generate_certificate_exception error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="create_tls_configuration_activity")
async def create_tls_configuration_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        hostname: str = params["hostname"]
        tls_config_dir: str = params.get("tls_config_dir", "infrastructure/orchestrator/config/docker/traefik/config/tls")
        certs_mount_path: str = params.get("certs_mount_path", "/certs")
        logger.info("event=create_tls_configuration_start hostname=%s tls_config_dir=%s", hostname, tls_config_dir)
        tls_config = {
            "tls": {
                "certificates": [{
                    "certFile": f"{certs_mount_path}/{hostname}.pem",
                    "keyFile": f"{certs_mount_path}/{hostname}-key.pem"
                }]
            }
        }
        config_file = Path(tls_config_dir) / f"{hostname}-tls.yml"
        with open(config_file, "w") as f:
            yaml.dump(tls_config, f, default_flow_style=False)
        logger.info("event=create_tls_configuration_complete hostname=%s config_file=%s", hostname, str(config_file))
        return {"success": True, "hostname": hostname, "config_file": str(config_file)}
    except Exception as e:
        logger.error("event=create_tls_configuration_failed error=%s", str(e))
        return {"success": False, "error": str(e)}


@activity.defn(name="configure_traefik_activity")
async def configure_traefik_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        traefik_compose_path: str = params["traefik_compose_path"]
        tls_strategy: str = params.get("tls_strategy", "local")
        email: str = params.get("acme_email", "admin@example.com")
        
        logger.info("event=configure_traefik_start strategy=%s path=%s", tls_strategy, traefik_compose_path)
        
        with open(traefik_compose_path, "r") as f:
            compose_config = yaml.safe_load(f)
            
        command = compose_config["services"]["traefik"]["command"]
        
        command = [cmd for cmd in command if not cmd.startswith("--certificatesresolvers")]
        
        if tls_strategy == "acme":
            command.extend([
                "--certificatesresolvers.myresolver.acme.tlschallenge=true",
                f"--certificatesresolvers.myresolver.acme.email={email}",
                "--certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json"
            ])
            logger.info("event=configure_traefik_acme_enabled")
        
        compose_config["services"]["traefik"]["command"] = command
        
        with open(traefik_compose_path, "w") as f:
            yaml.dump(compose_config, f, default_flow_style=False)
            
        return {"success": True, "strategy": tls_strategy}
    except Exception as e:
        logger.error("event=configure_traefik_failed error=%s", str(e))
        return {"success": False, "error": str(e)}
