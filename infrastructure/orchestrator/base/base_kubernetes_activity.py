from __future__ annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, TYPE_CHECKING
from pathlib import Path
import logging
import yaml
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
)
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from kubernetes import client  # type: ignore

def substitute_env_vars(text: str, env_dict: Dict[str, str]) -> str:
    import re
    if not isinstance(text, str):
        return text
    
    pattern = r'\$\{([^}]+)\}'
    
    def replacer(match):
        var_name = match.group(1)
        value = env_dict.get(var_name, os.environ.get(var_name, match.group(0)))
        return str(value)
    
    return re.sub(pattern, replacer, text)

def substitute_env_in_structure(data: Any, env_dict: Dict[str, str]) -> Any:
    if isinstance(data, dict):
        return {k: substitute_env_in_structure(v, env_dict) for k, v in data.items()}
    elif isinstance(data, list):
        return [substitute_env_in_structure(item, env_dict) for item in data]
    elif isinstance(data, str):
        return substitute_env_vars(data, env_dict)
    else:
        return data

@dataclass
class KubernetesConfig:
    api_version: str
    kind: str
    metadata: Dict[str, Any]
    spec: Dict[str, Any]
    
    @classmethod
    def from_yaml_file(cls, file_path: Union[str, Path], env_vars: Optional[Dict[str, str]] = None) -> "KubernetesConfig":
        file_path = Path(file_path)
        logger.debug("k8s_load_start file=%s", file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Kubernetes YAML file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            yaml_content = f.read()
        
        env_dict = env_vars or {}
        yaml_content = substitute_env_vars(yaml_content, env_dict)
        
        try:
            yaml_data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            logger.exception("k8s_yaml_error file=%s error=%s", file_path, e)
            raise
        
        yaml_data = substitute_env_in_structure(yaml_data, env_dict)
        
        return cls(
            api_version=yaml_data.get("apiVersion", ""),
            kind=yaml_data.get("kind", ""),
            metadata=yaml_data.get("metadata", {}),
            spec=yaml_data.get("spec", {})
        )

class BaseKubernetesManager(ABC):
    @abstractmethod
    def deploy(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        raise NotImplementedError

class KubernetesManager(BaseKubernetesManager):
    def __init__(self, deployment_config: KubernetesConfig, service_config: Optional[KubernetesConfig] = None, namespace: str = "default") -> None:
        self.deployment_config = deployment_config
        self.service_config = service_config
        self.namespace = namespace
        
        self.api_client = self._get_k8s_client()
        
        from kubernetes import client
        self.apps_v1 = client.AppsV1Api(self.api_client)
        self.core_v1 = client.CoreV1Api(self.api_client)
        
        logger.debug("k8s_manager_init namespace=%s", namespace)
    
    def _get_k8s_client(self):
        from kubernetes import client, config
        
        try:
            config.load_incluster_config()
            logger.debug("k8s_client_incluster")
        except:
            try:
                config.load_kube_config()
                logger.debug("k8s_client_kubeconfig")
            except Exception as e:
                logger.exception("k8s_client_error error=%s", e)
                raise
        
        return client.ApiClient()
    
    def deploy(self) -> None:
        from kubernetes import client
        
        logger.info("k8s_deploy_start namespace=%s", self.namespace)
        
        try:
            if self.deployment_config.kind == "Deployment":
                deployment_name = self.deployment_config.metadata.get("name")
                logger.debug("k8s_deploy_deployment name=%s", deployment_name)
                
                deployment_body = {
                    "apiVersion": self.deployment_config.api_version,
                    "kind": "Deployment",
                    "metadata": self.deployment_config.metadata,
                    "spec": self.deployment_config.spec
                }
                
                try:
                    self.apps_v1.read_namespaced_deployment(
                        name=deployment_name,
                        namespace=self.namespace
                    )
                    logger.info("k8s_deployment_exists_updating name=%s", deployment_name)
                    self.apps_v1.patch_namespaced_deployment(
                        name=deployment_name,
                        namespace=self.namespace,
                        body=deployment_body
                    )
                except client.exceptions.ApiException as e:
                    if e.status == 404:
                        logger.info("k8s_deployment_creating name=%s", deployment_name)
                        self.apps_v1.create_namespaced_deployment(
                            namespace=self.namespace,
                            body=deployment_body
                        )
                    else:
                        raise
            
            if self.service_config and self.service_config.kind == "Service":
                service_name = self.service_config.metadata.get("name")
                logger.debug("k8s_deploy_service name=%s", service_name)
                
                service_body = {
                    "apiVersion": self.service_config.api_version,
                    "kind": "Service",
                    "metadata": self.service_config.metadata,
                    "spec": self.service_config.spec
                }
                
                try:
                    self.core_v1.read_namespaced_service(
                        name=service_name,
                        namespace=self.namespace
                    )
                    logger.info("k8s_service_exists_updating name=%s", service_name)
                    self.core_v1.patch_namespaced_service(
                        name=service_name,
                        namespace=self.namespace,
                        body=service_body
                    )
                except client.exceptions.ApiException as e:
                    if e.status == 404:
                        logger.info("k8s_service_creating name=%s", service_name)
                        self.core_v1.create_namespaced_service(
                            namespace=self.namespace,
                            body=service_body
                        )
                    else:
                        raise
            
            logger.info("k8s_deploy_complete namespace=%s", self.namespace)
        
        except Exception as e:
            logger.exception("k8s_deploy_error namespace=%s error=%s", self.namespace, e)
            raise
    
    def delete(self) -> None:
        from kubernetes import client
        
        logger.info("k8s_delete_start namespace=%s", self.namespace)
        
        try:
            if self.deployment_config.kind == "Deployment":
                deployment_name = self.deployment_config.metadata.get("name")
                logger.info("k8s_delete_deployment name=%s", deployment_name)
                self.apps_v1.delete_namespaced_deployment(
                    name=deployment_name,
                    namespace=self.namespace
                )
            
            if self.service_config and self.service_config.kind == "Service":
                service_name = self.service_config.metadata.get("name")
                logger.info("k8s_delete_service name=%s", service_name)
                self.core_v1.delete_namespaced_service(
                    name=service_name,
                    namespace=self.namespace
                )
            
            logger.info("k8s_delete_complete namespace=%s", self.namespace)
        
        except Exception as e:
            logger.exception("k8s_delete_error namespace=%s error=%s", self.namespace, e)
            raise
    
    def get_status(self) -> Dict[str, Any]:
        logger.debug("k8s_status_start namespace=%s", self.namespace)
        
        status = {}
        
        try:
            if self.deployment_config.kind == "Deployment":
                deployment_name = self.deployment_config.metadata.get("name")
                deployment = self.apps_v1.read_namespaced_deployment_status(
                    name=deployment_name,
                    namespace=self.namespace
                )
                
                status["deployment"] = {
                    "name": deployment_name,
                    "replicas": deployment.status.replicas,
                    "ready_replicas": deployment.status.ready_replicas,
                    "available_replicas": deployment.status.available_replicas,
                    "updated_replicas": deployment.status.updated_replicas
                }
            
            logger.debug("k8s_status_complete namespace=%s", self.namespace)
            return status
        
        except Exception as e:
            logger.exception("k8s_status_error namespace=%s error=%s", self.namespace, e)
            return {"error": str(e)}

class KubernetesBaseService:
    def __init__(
        self,
        deployment_yaml_path: Union[str, Path],
        service_yaml_path: Optional[Union[str, Path]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        namespace: str = "default",
        instance_id: str = "1"
    ) -> None:
        self.deployment_yaml_path = Path(deployment_yaml_path)
        self.service_yaml_path = Path(service_yaml_path) if service_yaml_path else None
        self.namespace = namespace
        self.instance_id = instance_id
        
        self.env_vars = env_vars or {}
        if instance_id:
            self.env_vars["INSTANCE_ID"] = instance_id
        
        logger.debug("k8s_service_init deployment=%s namespace=%s instance=%s", 
                    deployment_yaml_path, namespace, instance_id)
        
        self.deployment_config = KubernetesConfig.from_yaml_file(
            self.deployment_yaml_path,
            self.env_vars
        )
        
        self.service_config = None
        if self.service_yaml_path:
            self.service_config = KubernetesConfig.from_yaml_file(
                self.service_yaml_path,
                self.env_vars
            )
        
        self.manager = KubernetesManager(
            deployment_config=self.deployment_config,
            service_config=self.service_config,
            namespace=namespace
        )
        
        logger.info("k8s_service_initialized namespace=%s instance=%s", namespace, instance_id)
    
    def deploy(self) -> None:
        logger.debug("k8s_service_deploy_start namespace=%s instance=%s", self.namespace, self.instance_id)
        try:
            self.manager.deploy()
            logger.debug("k8s_service_deploy_complete namespace=%s instance=%s", self.namespace, self.instance_id)
        except Exception as e:
            logger.exception("k8s_service_deploy_error namespace=%s instance=%s error=%s", 
                           self.namespace, self.instance_id, e)
            raise
    
    def delete(self) -> None:
        logger.debug("k8s_service_delete_start namespace=%s instance=%s", self.namespace, self.instance_id)
        try:
            self.manager.delete()
            logger.debug("k8s_service_delete_complete namespace=%s instance=%s", self.namespace, self.instance_id)
        except Exception as e:
            logger.exception("k8s_service_delete_error namespace=%s instance=%s error=%s", 
                           self.namespace, self.instance_id, e)
            raise
    
    def get_status(self) -> Dict[str, Any]:
        logger.debug("k8s_service_status_start namespace=%s instance=%s", self.namespace, self.instance_id)
        try:
            status = self.manager.get_status()
            logger.debug("k8s_service_status_complete namespace=%s instance=%s", self.namespace, self.instance_id)
            return status
        except Exception as e:
            logger.exception("k8s_service_status_error namespace=%s instance=%s error=%s", 
                           self.namespace, self.instance_id, e)
            return {"error": str(e)}
