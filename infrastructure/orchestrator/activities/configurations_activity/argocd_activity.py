import logging
import time
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig

logger = logging.getLogger(__name__)


class ArgoCDManager(BaseService):
    SERVICE_NAME = "ArgoCD"
    SERVICE_DESCRIPTION = "GitOps continuous delivery"
    DEFAULT_API_PORT = 8080
    DEFAULT_GRPC_PORT = 8083
    HEALTH_CHECK_TIMEOUT = 60

    def __init__(self):
        config = ContainerConfig(
            image="argoproj/argocd:latest",
            name="argocd-server",
            ports={
                8080: 31080,  # API Server
                8083: 31083,  # gRPC
            },
            volumes={
                "argocd-data": "/var/argocd",
                # Mount your Git repo config
                "/home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/config/argocd": "/etc/argocd/config"
            },
            network="monitoring-bridge",
            memory="512m",
            memory_reservation="256m",
            cpus=1.0,
            restart="unless-stopped",
            environment={
                "ARGOCD_SERVER_INSECURE": "true",  # For local development
            },
            command=[
                "argocd-server",
                "--insecure",
                "--staticassets", "/shared/app",
                "--repo-server", "argocd-repo-server:8081",
            ],
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    "wget --no-verbose --tries=1 --spider http://localhost:8080/healthz || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 5,
                "start_period": 60000000000
            }
        )
        super().__init__(config)

    def login(self, username: str = "admin", password: str = "admin") -> Dict[str, Any]:
        """Login to ArgoCD and get auth token"""
        command = f"argocd login localhost:31080 --username {username} --password {password} --insecure"
        exit_code, output = self.exec(command)
        return {
            "success": exit_code == 0,
            "output": output
        }

    def sync_application(self, app_name: str) -> Dict[str, Any]:
        """Sync an ArgoCD application (trigger deployment)"""
        command = f"argocd app sync {app_name} --insecure"
        exit_code, output = self.exec(command)
        return {
            "success": exit_code == 0,
            "app_name": app_name,
            "output": output
        }

    def get_application_status(self, app_name: str) -> Dict[str, Any]:
        """Get status of ArgoCD application"""
        command = f"argocd app get {app_name} --insecure -o json"
        exit_code, output = self.exec(command)
        return {
            "success": exit_code == 0,
            "app_name": app_name,
            "status": output
        }

    def create_application(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create new ArgoCD application from config"""
        app_name = app_config.get("name")
        repo_url = app_config.get("repo_url")
        path = app_config.get("path")
        dest_server = app_config.get("dest_server", "https://kubernetes.default.svc")
        dest_namespace = app_config.get("dest_namespace", "default")

        command = (
            f"argocd app create {app_name} "
            f"--repo {repo_url} "
            f"--path {path} "
            f"--dest-server {dest_server} "
            f"--dest-namespace {dest_namespace} "
            f"--insecure"
        )
        exit_code, output = self.exec(command)
        return {
            "success": exit_code == 0,
            "app_name": app_name,
            "output": output
        }

    def list_applications(self) -> Dict[str, Any]:
        """List all ArgoCD applications"""
        command = "argocd app list --insecure -o json"
        exit_code, output = self.exec(command)
        return {
            "success": exit_code == 0,
            "output": output
        }


class ArgoCDRepoServerManager(BaseService):
    """ArgoCD Repository Server (required for ArgoCD to work)"""
    SERVICE_NAME = "ArgoCD-RepoServer"
    SERVICE_DESCRIPTION = "ArgoCD repository server"
    DEFAULT_PORT = 8081

    def __init__(self):
        config = ContainerConfig(
            image="argoproj/argocd:latest",
            name="argocd-repo-server",
            ports={8081: 31081},
            volumes={
                "argocd-repo-data": "/var/argocd/repo",
            },
            network="monitoring-bridge",
            memory="256m",
            memory_reservation="128m",
            cpus=0.5,
            restart="unless-stopped",
            command=["argocd-repo-server"],
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    "netstat -an | grep 8081 || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 40000000000
            }
        )
        super().__init__(config)


@activity.defn
async def start_argocd_repo_server_activity(params: Dict[str, Any]) -> bool:
    """Start ArgoCD Repository Server (must start before main server)"""
    logger.info("Starting ArgoCD Repository Server")
    manager = ArgoCDRepoServerManager()
    manager.run()
    logger.info("ArgoCD Repository Server started successfully")
    # Wait for repo server to be ready
    time.sleep(5)
    return True


@activity.defn
async def start_argocd_server_activity(params: Dict[str, Any]) -> bool:
    """Start ArgoCD Server"""
    logger.info("Starting ArgoCD Server")
    manager = ArgoCDManager()
    manager.run()
    logger.info("ArgoCD Server started successfully")
    # Wait for server to be ready
    time.sleep(10)
    return True


@activity.defn
async def stop_argocd_activity(params: Dict[str, Any]) -> bool:
    """Stop ArgoCD containers"""
    logger.info("Stopping ArgoCD")
    
    # Stop server first
    server_manager = ArgoCDManager()
    server_manager.stop(timeout=30)
    
    # Then stop repo server
    repo_manager = ArgoCDRepoServerManager()
    repo_manager.stop(timeout=30)
    
    logger.info("ArgoCD stopped successfully")
    return True


@activity.defn
async def delete_argocd_activity(params: Dict[str, Any]) -> bool:
    """Delete ArgoCD containers"""
    logger.info("Deleting ArgoCD")
    
    server_manager = ArgoCDManager()
    server_manager.delete(force=False)
    
    repo_manager = ArgoCDRepoServerManager()
    repo_manager.delete(force=False)
    
    logger.info("ArgoCD deleted successfully")
    return True


@activity.defn
async def argocd_login_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    """Login to ArgoCD"""
    logger.info("ArgoCD login activity")
    manager = ArgoCDManager()
    username = params.get("username", "admin")
    password = params.get("password", "admin")
    result = manager.login(username, password)
    logger.info("ArgoCD login result: %s", result)
    return result


@activity.defn
async def argocd_sync_application_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    """Sync ArgoCD application (deploy)"""
    app_name = params.get("app_name")
    if not app_name:
        raise ValueError("app_name is required")
    
    logger.info("Syncing ArgoCD application: %s", app_name)
    manager = ArgoCDManager()
    result = manager.sync_application(app_name)
    logger.info("Sync result: %s", result)
    return result


@activity.defn
async def argocd_get_app_status_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get ArgoCD application status"""
    app_name = params.get("app_name")
    if not app_name:
        raise ValueError("app_name is required")
    
    logger.info("Getting status for ArgoCD application: %s", app_name)
    manager = ArgoCDManager()
    result = manager.get_application_status(app_name)
    logger.info("Status result: %s", result)
    return result


@activity.defn
async def argocd_create_application_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create new ArgoCD application"""
    app_config = params.get("app_config")
    if not app_config:
        raise ValueError("app_config is required")
    
    logger.info("Creating ArgoCD application: %s", app_config)
    manager = ArgoCDManager()
    result = manager.create_application(app_config)
    logger.info("Create result: %s", result)
    return result


@activity.defn
async def argocd_list_applications_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    """List all ArgoCD applications"""
    logger.info("Listing ArgoCD applications")
    manager = ArgoCDManager()
    result = manager.list_applications()
    logger.info("List result: %s", result)
    return result