# infrastructure/database/shared/base_database_setup.py
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess

from infrastructure.orchestrator.base import YAMLContainerManager, ContainerState
from infrastructure.orchestrator.activities.network import (
    generate_certificates_activity,
    verify_certificates_activity,
    generate_traefik_tls_config_activity,
    add_hosts_entries_activity,
    verify_hosts_entries_activity,
)

logger = logging.getLogger(__name__)


class BaseDatabaseSetupActivity:
    """Base class for database setup activities with built-in network setup"""
    
    def __init__(
        self,
        service_name: str,
        compose_file: str,
        hostname: str,
        ip: str,
        certs_dir: Optional[str] = None,
        skip_certificates: bool = False,
        skip_hosts: bool = False,
        max_startup_wait: int = 60,
        health_check_interval: int = 5,
    ):
        self.service_name = service_name
        self.compose_file = Path(compose_file)
        self.hostname = hostname
        self.ip = ip
        self.certs_dir = Path(certs_dir) if certs_dir else Path(__file__).parent.parent.parent / "orchestrator" / "config" / "docker" / "traefik" / "certs"
        self.skip_certificates = skip_certificates
        self.skip_hosts = skip_hosts
        self.max_startup_wait = max_startup_wait
        self.health_check_interval = health_check_interval
        
        logger.info(
            f"event=base_database_setup_init service={service_name} "
            f"compose_file={compose_file} hostname={hostname} ip={ip}"
        )

    async def _ensure_network(self, network_name: str = "database-network") -> bool:
        """Ensure the required Docker network exists"""
        try:
            result = subprocess.run(
                ["docker", "network", "inspect", network_name],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.info(f"event=creating_network service={self.service_name} network={network_name}")
                create_result = subprocess.run(
                    ["docker", "network", "create", network_name],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if create_result.returncode == 0:
                    logger.info(f"event=network_created service={self.service_name} network={network_name}")
                    return True
                else:
                    logger.error(
                        f"event=network_create_failed service={self.service_name} "
                        f"network={network_name} error={create_result.stderr}"
                    )
                    return False
            
            logger.info(f"event=network_exists service={self.service_name} network={network_name}")
            return True
            
        except Exception as e:
            logger.exception(f"event=network_check_failed service={self.service_name} error={e}")
            return False

    async def _setup_certificates(self, trace_id: str) -> bool:
        """Setup TLS certificates for the service"""
        if self.skip_certificates:
            logger.info(f"event=certificates_skipped service={self.service_name} trace_id={trace_id}")
            return True
        
        try:
            # Generate certificates
            cert_result = await generate_certificates_activity({
                "hostnames": [self.hostname],
                "certs_dir": str(self.certs_dir),
                "trace_id": trace_id,
                "use_mkcert": True,
                "validity_days": 365,
            })
            
            if not cert_result.get("success"):
                logger.error(
                    f"event=certificate_generation_failed service={self.service_name} "
                    f"trace_id={trace_id} result={cert_result}"
                )
                return False
            
            # Verify certificates
            verify_result = await verify_certificates_activity({
                "hostnames": [self.hostname],
                "certs_dir": str(self.certs_dir),
                "trace_id": trace_id,
            })
            
            if not verify_result.get("success"):
                logger.error(
                    f"event=certificate_verification_failed service={self.service_name} "
                    f"trace_id={trace_id} result={verify_result}"
                )
                return False
            
            # Generate Traefik TLS config
            tls_config_path = self.certs_dir.parent / "config" / "tls" / f"{self.service_name}_tls.yaml"
            tls_result = await generate_traefik_tls_config_activity({
                "hostnames": [self.hostname],
                "certs_dir": "/certs",  # Path inside Traefik container
                "output_file": str(tls_config_path),
                "trace_id": trace_id,
            })
            
            if not tls_result.get("success"):
                logger.error(
                    f"event=traefik_tls_config_failed service={self.service_name} "
                    f"trace_id={trace_id} result={tls_result}"
                )
                return False
            
            logger.info(f"event=certificates_setup_complete service={self.service_name} trace_id={trace_id}")
            return True
            
        except Exception as e:
            logger.exception(
                f"event=certificate_setup_failed service={self.service_name} "
                f"trace_id={trace_id} error={e}"
            )
            return False

    async def _setup_hosts(self, trace_id: str) -> bool:
        """Setup /etc/hosts entries for the service"""
        if self.skip_hosts:
            logger.info(f"event=hosts_setup_skipped service={self.service_name} trace_id={trace_id}")
            return True
        
        try:
            # Add hosts entry
            hosts_result = await add_hosts_entries_activity({
                "entries": [{"ip": self.ip, "hostname": self.hostname}],
                "trace_id": trace_id,
                "force_replace": True,
            })
            
            if not hosts_result.get("success"):
                logger.error(
                    f"event=hosts_add_failed service={self.service_name} "
                    f"trace_id={trace_id} result={hosts_result}"
                )
                return False
            
            # Verify hosts entry
            verify_result = await verify_hosts_entries_activity({
                "hostnames": [self.hostname],
                "trace_id": trace_id,
            })
            
            if not verify_result.get("success"):
                logger.error(
                    f"event=hosts_verification_failed service={self.service_name} "
                    f"trace_id={trace_id} result={verify_result}"
                )
                return False
            
            logger.info(f"event=hosts_setup_complete service={self.service_name} trace_id={trace_id}")
            return True
            
        except Exception as e:
            logger.exception(
                f"event=hosts_setup_failed service={self.service_name} "
                f"trace_id={trace_id} error={e}"
            )
            return False

    async def _pre_pull_images(self, trace_id: str) -> bool:
        """Pre-pull Docker images to avoid timeout during startup"""
        try:
            # Extract image from compose file
            import yaml
            with open(self.compose_file, 'r') as f:
                compose_config = yaml.safe_load(f)
            
            services = compose_config.get('services', {})
            images = []
            
            for service_name, service_config in services.items():
                if 'image' in service_config:
                    images.append(service_config['image'])
            
            if not images:
                logger.warning(f"event=no_images_found service={self.service_name} trace_id={trace_id}")
                return True
            
            logger.info(
                f"event=pre_pulling_images trace_id={trace_id} "
                f"service={self.service_name} images={images}"
            )
            
            for image in images:
                for attempt in range(3):
                    logger.info(
                        f"event=pulling_image trace_id={trace_id} "
                        f"service={self.service_name} image={image} attempt={attempt + 1}"
                    )
                    
                    result = subprocess.run(
                        ["docker", "pull", image],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    if result.returncode == 0:
                        logger.info(
                            f"event=image_pulled trace_id={trace_id} "
                            f"service={self.service_name} image={image}"
                        )
                        break
                    else:
                        if attempt == 2:
                            logger.error(
                                f"event=image_pull_failed trace_id={trace_id} "
                                f"service={self.service_name} image={image} error={result.stderr}"
                            )
                            return False
                        time.sleep(5)
            
            return True
            
        except Exception as e:
            logger.exception(
                f"event=pre_pull_failed service={self.service_name} "
                f"trace_id={trace_id} error={e}"
            )
            return False

    async def _wait_for_healthy(
        self,
        manager: YAMLContainerManager,
        trace_id: str
    ) -> bool:
        """Wait for container to become healthy with proper status checks"""
        waited = 0
        
        while waited < self.max_startup_wait:
            status = manager.get_status()
            
            logger.debug(
                f"event=health_check service={self.service_name} "
                f"trace_id={trace_id} status={status.value} waited={waited}"
            )
            
            if status == ContainerState.RUNNING:
                # Additional verification: check if service is actually responding
                if await self._verify_service_responsive(trace_id):
                    logger.info(
                        f"event=service_healthy service={self.service_name} "
                        f"trace_id={trace_id} waited={waited}"
                    )
                    return True
            elif status in [ContainerState.EXITED, ContainerState.DEAD]:
                logger.error(
                    f"event=service_failed service={self.service_name} "
                    f"trace_id={trace_id} status={status.value}"
                )
                return False
            
            time.sleep(self.health_check_interval)
            waited += self.health_check_interval
        
        logger.error(
            f"event=health_check_timeout service={self.service_name} "
            f"trace_id={trace_id} waited={waited}"
        )
        return False

    async def _verify_service_responsive(self, trace_id: str) -> bool:

        try:

            result = subprocess.run(
                ["docker", "exec", f"{self.service_name}-instance-0", "sh", "-c", 
                 "wget -q -O- http://localhost:6333/healthz || curl -f http://localhost:6333/healthz"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            
            is_responsive = result.returncode == 0
            logger.info(
                f"event=service_responsiveness_check service={self.service_name} "
                f"trace_id={trace_id} responsive={is_responsive}"
            )
            return is_responsive
            
        except Exception as e:
            logger.warning(
                f"event=responsiveness_check_failed service={self.service_name} "
                f"trace_id={trace_id} error={e}"
            )
            return False

    async def setup_service(self, env_vars: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Main setup method that orchestrates all setup steps"""
        start_time = time.time()
        trace_id = f"{self.service_name}-{int(time.time())}"
        
        logger.info(
            f"event=setup_start trace_id={trace_id} service={self.service_name} "
            f"hostname={self.hostname} ip={self.ip}"
        )
        
        try:
            # Step 1: Ensure network exists
            if not await self._ensure_network():
                return {
                    "success": False,
                    "service": self.service_name,
                    "error": "Failed to create/verify network",
                    "trace_id": trace_id,
                }
            
            # Step 2: Pre-pull images
            if not await self._pre_pull_images(trace_id):
                logger.warning(
                    f"event=image_pull_warning service={self.service_name} "
                    f"trace_id={trace_id} message=continuing_despite_pull_failure"
                )
            
            # Step 3: Setup certificates
            if not await self._setup_certificates(trace_id):
                return {
                    "success": False,
                    "service": self.service_name,
                    "error": "Certificate setup failed",
                    "trace_id": trace_id,
                }
            
            # Step 4: Setup hosts
            if not await self._setup_hosts(trace_id):
                return {
                    "success": False,
                    "service": self.service_name,
                    "error": "Hosts setup failed",
                    "trace_id": trace_id,
                }
            
            # Step 5: Start container
            manager = YAMLContainerManager(
                str(self.compose_file),
                instance_id=0,
                env_vars=env_vars or {}
            )
            
            # Stop and clean up existing container if any
            current_status = manager.get_status()
            if current_status != ContainerState.NOT_FOUND:
                logger.info(
                    f"event=cleanup_existing service={self.service_name} "
                    f"trace_id={trace_id} current_status={current_status.value}"
                )
                manager.stop(force=True)
                manager.delete(remove_volumes=False, remove_images=True, remove_networks=False)
            
            # Start the container
            if not manager.start(restart_if_running=True):
                return {
                    "success": False,
                    "service": self.service_name,
                    "error": "Container start failed",
                    "trace_id": trace_id,
                    "status": manager.get_status().value,
                }
            
            # Step 6: Wait for healthy state
            if not await self._wait_for_healthy(manager, trace_id):
                return {
                    "success": False,
                    "service": self.service_name,
                    "error": "Service did not become healthy",
                    "trace_id": trace_id,
                    "status": manager.get_status().value,
                }
            
            # Success
            duration_ms = int((time.time() - start_time) * 1000)
            final_status = manager.get_status()
            
            logger.info(
                f"event=setup_complete trace_id={trace_id} service={self.service_name} "
                f"success=True duration_ms={duration_ms} status={final_status.value}"
            )
            
            return {
                "success": True,
                "service": self.service_name,
                "trace_id": trace_id,
                "hostname": self.hostname,
                "ip": self.ip,
                "status": final_status.value,
                "duration_ms": duration_ms,
                "url": f"https://{self.hostname}",
            }
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.exception(
                f"event=setup_failed service={self.service_name} "
                f"trace_id={trace_id} error={e} duration_ms={duration_ms}"
            )
            
            return {
                "success": False,
                "service": self.service_name,
                "error": str(e),
                "trace_id": trace_id,
                "duration_ms": duration_ms,
            }

    async def teardown_service(self) -> Dict[str, Any]:
        """Teardown the service and clean up resources"""
        start_time = time.time()
        trace_id = f"{self.service_name}-teardown-{int(time.time())}"
        
        logger.info(
            f"event=teardown_start trace_id={trace_id} service={self.service_name}"
        )
        
        try:
            manager = YAMLContainerManager(str(self.compose_file), instance_id=0)
            
            # Stop container
            manager.stop(force=True)
            
            # Delete container and resources
            success = manager.delete(
                remove_volumes=True,
                remove_images=True,
                remove_networks=False
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                f"event=teardown_complete trace_id={trace_id} service={self.service_name} "
                f"success={success} duration_ms={duration_ms}"
            )
            
            return {
                "success": success,
                "service": self.service_name,
                "trace_id": trace_id,
                "duration_ms": duration_ms,
            }
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.exception(
                f"event=teardown_failed service={self.service_name} "
                f"trace_id={trace_id} error={e} duration_ms={duration_ms}"
            )
            
            return {
                "success": False,
                "service": self.service_name,
                "error": str(e),
                "trace_id": trace_id,
                "duration_ms": duration_ms,
            }