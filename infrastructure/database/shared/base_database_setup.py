import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path
from temporalio import activity

from infrastructure.orchestrator.base.base_container_activity import YAMLContainerManager, ContainerState
from infrastructure.orchestrator.base.logql_logger import LogQLLogger

logger = logging.getLogger(__name__)

class BaseDatabaseSetupActivity:
    """
    Base class for database setup activities.
    Uses YAMLContainerManager via composition to handle Docker lifecycle.
    """
    
    def __init__(self, service_name: str, compose_file: str, hostname: str, ip: str):
        self.service_name = service_name
        self.compose_file = Path(compose_file)
        self.hostname = hostname
        self.ip = ip
        self.log = LogQLLogger(f"{__name__}.{self.__class__.__name__}")
        self.trace_id = self.log.set_trace_id()

    async def setup_service(self, env_vars: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Orchestrates the setup of a database service.
        Note: Network, Certs, and Hosts are handled by the Workflow before calling this.
        This method focuses on converting the Compose file and running the container.
        """
        start_time = time.time()
        
        self.log.info(
            "setup_service_start", 
            service=self.service_name, 
            hostname=self.hostname, 
            ip=self.ip
        )

        try:
            if not self.compose_file.exists():
                raise FileNotFoundError(f"Compose file not found: {self.compose_file}")

            # Instantiate Manager
            manager = YAMLContainerManager(
                yaml_path=str(self.compose_file),
                instance_id=0, # Assuming single instance per cell for now
                env_vars=env_vars or {}
            )

            # 1. Stop existing if running (clean slate)
            manager.stop(force=True)
            manager.delete(remove_volumes=False) # Persist data!

            # 2. Start Service
            success = manager.start(restart_if_running=True)
            
            if not success:
                raise Exception(f"Failed to start service: {self.service_name}")

            # 3. Verify Health
            status = manager.get_status()
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            self.log.info(
                "setup_service_complete",
                service=self.service_name,
                duration_ms=duration_ms,
                status=status.value
            )

            return {
                "success": True,
                "service": self.service_name,
                "hostname": self.hostname,
                "ip": self.ip,
                "status": status.value,
                "duration_ms": duration_ms
            }

        except Exception as e:
            self.log.exception("setup_service_failed", error=e)
            return {
                "success": False,
                "service": self.service_name,
                "error": str(e)
            }

    async def teardown_service(self) -> Dict[str, Any]:
        """
        Stops and removes the service container.
        Preserves volumes.
        """
        try:
            manager = YAMLContainerManager(
                yaml_path=str(self.compose_file),
                instance_id=0
            )
            
            stopped = manager.stop(force=True)
            deleted = manager.delete(remove_volumes=False)
            
            return {
                "success": stopped and deleted,
                "service": self.service_name
            }
        except Exception as e:
            self.log.exception("teardown_service_failed", error=e)
            return {
                "success": False,
                "service": self.service_name,
                "error": str(e)
            }
