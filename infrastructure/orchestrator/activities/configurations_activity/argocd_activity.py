from typing import Dict, Any
from pathlib import Path
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import YAMLBaseService
from infrastructure.orchestrator.base.port_manager import get_port_manager
from infrastructure.orchestrator.base.logql_logger import LogQLLogger, trace_operation

log = LogQLLogger(__name__)

class ArgoCDRepoManager(YAMLBaseService):
    SERVICE_NAME = "ArgoCDRepo"
    SERVICE_DESCRIPTION = "argocd repository server"
    
    _yaml_file_cache = None
    __slots__ = ('_port', '_instance_id')
    
    def __init__(self, instance_id: int = 0) -> None:
        trace_id = log.set_trace_id()
        log.debug("manager_init_start", service="argocd-repo", instance=instance_id, trace_id=trace_id)
        
        pm = get_port_manager()
        repo_port = pm.get_port("argocd-repo", instance_id, "port")
        self._port = repo_port
        self._instance_id = instance_id
        
        if not ArgoCDRepoManager._yaml_file_cache:
            ArgoCDRepoManager._yaml_file_cache = Path(__file__).parent.parent.parent / "config" / "docker" / "argocd-repo-dynamic-docker.yaml"
        
        env_vars = {
            "ARGOCD_REPO_PORT": str(repo_port),
            "INSTANCE_ID": str(instance_id)
        }
        
        log.debug("yaml_loading", yaml_file=str(ArgoCDRepoManager._yaml_file_cache))
        
        super().__init__(
            yaml_file_path=ArgoCDRepoManager._yaml_file_cache,
            service_name="argocd-repo-server",
            env_vars=env_vars,
            instance_id=str(instance_id)
        )
        
        log.info("manager_ready", service="argocd-repo", instance=instance_id, port=repo_port, container=self.config.container_name)

class ArgoCDServerManager(YAMLBaseService):
    SERVICE_NAME = "ArgoCDServer"
    SERVICE_DESCRIPTION = "argocd api server"
    
    _yaml_file_cache = None
    __slots__ = ('_port', '_instance_id')
    
    def __init__(self, instance_id: int = 0) -> None:
        trace_id = log.set_trace_id()
        log.debug("manager_init_start", service="argocd-server", instance=instance_id, trace_id=trace_id)
        
        pm = get_port_manager()
        server_port = pm.get_port("argocd-server", instance_id, "port")
        self._port = server_port
        self._instance_id = instance_id
        
        if not ArgoCDServerManager._yaml_file_cache:
            ArgoCDServerManager._yaml_file_cache = Path(__file__).parent.parent.parent / "config" / "docker" / "argocd-server-dynamic-docker.yaml"
        
        env_vars = {
            "ARGOCD_SERVER_PORT": str(server_port),
            "INSTANCE_ID": str(instance_id)
        }
        
        log.debug("yaml_loading", yaml_file=str(ArgoCDServerManager._yaml_file_cache))
        
        super().__init__(
            yaml_file_path=ArgoCDServerManager._yaml_file_cache,
            service_name="argocd-server",
            env_vars=env_vars,
            instance_id=str(instance_id)
        )
        
        log.info("manager_ready", service="argocd-server", instance=instance_id, port=server_port, container=self.config.container_name)

@activity.defn
@trace_operation("start_argocd_repo")
async def start_argocd_repo_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="start_argocd_repo", instance=instance_id)
    ArgoCDRepoManager(instance_id=instance_id).run()
    log.info("activity_complete", activity="start_argocd_repo", instance=instance_id)
    return True

@activity.defn
@trace_operation("stop_argocd_repo")
async def stop_argocd_repo_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="stop_argocd_repo", instance=instance_id)
    ArgoCDRepoManager(instance_id=instance_id).stop(timeout=30)
    log.info("activity_complete", activity="stop_argocd_repo", instance=instance_id)
    return True

@activity.defn
@trace_operation("start_argocd_server")
async def start_argocd_server_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="start_argocd_server", instance=instance_id)
    ArgoCDServerManager(instance_id=instance_id).run()
    log.info("activity_complete", activity="start_argocd_server", instance=instance_id)
    return True

@activity.defn
@trace_operation("stop_argocd_server")
async def stop_argocd_server_activity(params: Dict[str, Any]) -> bool:
    instance_id = params.get("instance_id", 0)
    log.info("activity_start", activity="stop_argocd_server", instance=instance_id)
    ArgoCDServerManager(instance_id=instance_id).stop(timeout=30)
    log.info("activity_complete", activity="stop_argocd_server", instance=instance_id)
    return True
