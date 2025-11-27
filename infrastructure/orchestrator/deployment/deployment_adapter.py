import os
import logging
from typing import Dict, Any, Protocol
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class DeploymentBackend(Protocol):
    def deploy(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        ...
    
    def stop(self, service_name: str) -> Dict[str, Any]:
        ...
    
    def restart(self, service_name: str) -> Dict[str, Any]:
        ...
    
    def delete(self, service_name: str) -> Dict[str, Any]:
        ...
    
    def status(self, service_name: str) -> Dict[str, Any]:
        ...


class DockerDeployer:
    def __init__(self):
        logger.info("deployment_backend_init", backend="docker")
    
    def deploy(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(
            "docker_deploy",
            service_name=service_name,
            has_config=bool(config)
        )
        
        import docker
        client = docker.from_env()
        
        try:
            container = client.containers.get(service_name)
            logger.info("docker_container_exists", service_name=service_name)
            
            if container.status != "running":
                container.start()
                logger.info("docker_container_started", service_name=service_name)
            
            return {"success": True, "method": "docker", "status": "running"}
        
        except docker.errors.NotFound:
            logger.info("docker_creating_container", service_name=service_name)
            
            container = client.containers.run(
                detach=True,
                **config
            )
            
            logger.info(
                "docker_container_created",
                service_name=service_name,
                container_id=container.id[:12]
            )
            
            return {"success": True, "method": "docker", "status": "created"}
    
    def stop(self, service_name: str) -> Dict[str, Any]:
        logger.info("docker_stop", service_name=service_name)
        
        import docker
        client = docker.from_env()
        
        try:
            container = client.containers.get(service_name)
            container.stop()
            logger.info("docker_stopped", service_name=service_name)
            return {"success": True}
        except Exception as e:
            logger.error("docker_stop_failed", service_name=service_name, error=str(e))
            return {"success": False, "error": str(e)}
    
    def restart(self, service_name: str) -> Dict[str, Any]:
        logger.info("docker_restart", service_name=service_name)
        
        import docker
        client = docker.from_env()
        
        try:
            container = client.containers.get(service_name)
            container.restart()
            logger.info("docker_restarted", service_name=service_name)
            return {"success": True}
        except Exception as e:
            logger.error("docker_restart_failed", service_name=service_name, error=str(e))
            return {"success": False, "error": str(e)}
    
    def delete(self, service_name: str) -> Dict[str, Any]:
        logger.info("docker_delete", service_name=service_name)
        
        import docker
        client = docker.from_env()
        
        try:
            container = client.containers.get(service_name)
            container.remove(force=True)
            logger.info("docker_deleted", service_name=service_name)
            return {"success": True}
        except Exception as e:
            logger.error("docker_delete_failed", service_name=service_name, error=str(e))
            return {"success": False, "error": str(e)}
    
    def status(self, service_name: str) -> Dict[str, Any]:
        import docker
        client = docker.from_env()
        
        try:
            container = client.containers.get(service_name)
            return {
                "success": True,
                "status": container.status,
                "id": container.id[:12]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class KubernetesDeployer:
    def __init__(self):
        logger.info("deployment_backend_init", backend="kubernetes")
        self.namespace = os.getenv("K8S_NAMESPACE", "observability")
    
    def deploy(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(
            "k8s_deploy",
            service_name=service_name,
            namespace=self.namespace
        )
        
        import subprocess
        
        manifest_path = config.get("manifest_path")
        if not manifest_path:
            logger.error("k8s_deploy_missing_manifest", service_name=service_name)
            return {"success": False, "error": "missing_manifest_path"}
        
        try:
            result = subprocess.run(
                ["kubectl", "apply", "-f", manifest_path, "-n", self.namespace],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info(
                    "k8s_deployed",
                    service_name=service_name,
                    namespace=self.namespace
                )
                return {"success": True, "method": "kubernetes", "output": result.stdout}
            else:
                logger.error(
                    "k8s_deploy_failed",
                    service_name=service_name,
                    stderr=result.stderr
                )
                return {"success": False, "error": result.stderr}
        
        except Exception as e:
            logger.error("k8s_deploy_error", service_name=service_name, error=str(e))
            return {"success": False, "error": str(e)}
    
    def stop(self, service_name: str) -> Dict[str, Any]:
        logger.info("k8s_scale_down", service_name=service_name)
        
        import subprocess
        
        try:
            result = subprocess.run(
                ["kubectl", "scale", "deployment", service_name, "--replicas=0", "-n", self.namespace],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {"success": result.returncode == 0, "output": result.stdout}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def restart(self, service_name: str) -> Dict[str, Any]:
        logger.info("k8s_rollout_restart", service_name=service_name)
        
        import subprocess
        
        try:
            result = subprocess.run(
                ["kubectl", "rollout", "restart", "deployment", service_name, "-n", self.namespace],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {"success": result.returncode == 0, "output": result.stdout}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete(self, service_name: str) -> Dict[str, Any]:
        logger.info("k8s_delete", service_name=service_name)
        
        import subprocess
        
        try:
            result = subprocess.run(
                ["kubectl", "delete", "deployment", service_name, "-n", self.namespace],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {"success": result.returncode == 0, "output": result.stdout}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def status(self, service_name: str) -> Dict[str, Any]:
        import subprocess
        
        try:
            result = subprocess.run(
                ["kubectl", "get", "deployment", service_name, "-n", self.namespace, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                return {
                    "success": True,
                    "replicas": data.get("status", {}).get("replicas", 0),
                    "ready_replicas": data.get("status", {}).get("readyReplicas", 0)
                }
            return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}


class DeploymentAdapter:
    def __init__(self):
        self.target = os.getenv("DEPLOY_TARGET", "docker")
        logger.info("deployment_adapter_init", target=self.target)
        
        if self.target == "docker":
            self.backend = DockerDeployer()
        elif self.target == "kubernetes":
            self.backend = KubernetesDeployer()
        else:
            logger.error("deployment_invalid_target", target=self.target)
            raise ValueError(f"Invalid DEPLOY_TARGET: {self.target}")
    
    def deploy(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        return self.backend.deploy(service_name, config)
    
    def stop(self, service_name: str) -> Dict[str, Any]:
        return self.backend.stop(service_name)
    
    def restart(self, service_name: str) -> Dict[str, Any]:
        return self.backend.restart(service_name)
    
    def delete(self, service_name: str) -> Dict[str, Any]:
        return self.backend.delete(service_name)
    
    def status(self, service_name: str) -> Dict[str, Any]:
        return self.backend.status(service_name)
