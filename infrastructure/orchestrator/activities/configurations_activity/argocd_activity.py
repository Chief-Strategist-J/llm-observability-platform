import logging
import time
from typing import Dict, Any
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.base.port_manager import get_port_manager

logger = logging.getLogger(__name__)


class ArgoCDManager(BaseService):
    SERVICE_NAME = "ArgoCD"
    SERVICE_DESCRIPTION = "GitOps continuous delivery"
    HEALTH_CHECK_TIMEOUT = 60

    def __init__(self, instance_id: int = 0):
        pm = get_port_manager()

        api_port = pm.get_port("argocd", instance_id, "server_port")
        repo_port = pm.get_port("argocd", instance_id, "repo_server_port")
        grpc_port = api_port + 3

        config = ContainerConfig(
            image="argoproj/argocd:latest",
            name=f"argocd-server-instance-{instance_id}",
            ports={
                api_port: api_port,
                grpc_port: grpc_port
            },
            volumes={
                "argocd-data": "/var/argocd",
                "/home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/config/argocd":
                    "/etc/argocd/config"
            },
            network="monitoring-bridge",
            memory="512m",
            memory_reservation="256m",
            cpus=1.0,
            restart="unless-stopped",
            environment={
                "ARGOCD_SERVER_INSECURE": "true"
            },
            command=[
                "argocd-server",
                "--insecure",
                "--staticassets", "/shared/app",
                f"--repo-server=argocd-repo-server:{repo_port}"
            ],
            healthcheck={
                "test": [
                    "CMD-SHELL",
                    f"wget --no-verbose --tries=1 --spider http://localhost:{api_port}/healthz || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 5,
                "start_period": 60000000000
            }
        )

        logger.info(
            "event=argocd_manager_init service=argocd instance=%s api_port=%s grpc_port=%s repo_port=%s",
            instance_id, api_port, grpc_port, repo_port
        )

        super().__init__(config)

    def login(self, username: str = "admin", password: str = "admin") -> Dict[str, Any]:
        api_port = list(self.config.ports.keys())[0]
        command = f"argocd login localhost:{api_port} --username {username} --password {password} --insecure"
        code, out = self.exec(command)
        return {"success": code == 0, "output": out}

    def sync_application(self, app_name: str) -> Dict[str, Any]:
        command = f"argocd app sync {app_name} --insecure"
        code, out = self.exec(command)
        return {"success": code == 0, "app_name": app_name, "output": out}

    def get_application_status(self, app_name: str) -> Dict[str, Any]:
        command = f"argocd app get {app_name} --insecure -o json"
        code, out = self.exec(command)
        return {"success": code == 0, "app_name": app_name, "status": out}

    def create_application(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        app_name = app_config["name"]
        repo_url = app_config["repo_url"]
        path = app_config["path"]
        dest_server = app_config.get("dest_server", "https://kubernetes.default.svc")
        dest_namespace = app_config.get("dest_namespace", "default")

        command = (
            f"argocd app create {app_name} "
            f"--repo {repo_url} "
            f"--path {path} "
            f"--dest-server {dest_server} "
            f"--dest-namespace {dest_namespace} --insecure"
        )
        code, out = self.exec(command)
        return {"success": code == 0, "app_name": app_name, "output": out}

    def list_applications(self) -> Dict[str, Any]:
        code, out = self.exec("argocd app list --insecure -o json")
        return {"success": code == 0, "output": out}


class ArgoCDRepoServerManager(BaseService):
    SERVICE_NAME = "ArgoCD-RepoServer"
    SERVICE_DESCRIPTION = "ArgoCD repository server"

    def __init__(self, instance_id: int = 0):
        pm = get_port_manager()

        repo_port = pm.get_port("argocd", instance_id, "repo_server_port")

        config = ContainerConfig(
            image="argoproj/argocd:latest",
            name=f"argocd-repo-server-instance-{instance_id}",
            ports={repo_port: repo_port},
            volumes={
                "argocd-repo-data": "/var/argocd/repo"
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
                    f"netstat -an | grep {repo_port} || exit 1"
                ],
                "interval": 30000000000,
                "timeout": 10000000000,
                "retries": 3,
                "start_period": 40000000000
            }
        )

        logger.info(
            "event=argocd_repo_init service=argocd_repo instance=%s repo_port=%s",
            instance_id, repo_port
        )

        super().__init__(config)

@activity.defn
async def start_argocd_repo_server_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=argocd_repo_start params=%s", params)
    manager = ArgoCDRepoServerManager()
    manager.run()
    logger.info("event=argocd_repo_started")
    time.sleep(5)
    return True


@activity.defn
async def start_argocd_server_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=argocd_server_start params=%s", params)
    manager = ArgoCDManager()
    manager.run()
    logger.info("event=argocd_server_started")
    time.sleep(10)
    return True


@activity.defn
async def stop_argocd_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=argocd_stop_begin")
    ArgoCDManager().stop(timeout=30)
    ArgoCDRepoServerManager().stop(timeout=30)
    logger.info("event=argocd_stop_complete")
    return True


@activity.defn
async def delete_argocd_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=argocd_delete_begin")
    ArgoCDManager().delete(force=False)
    ArgoCDRepoServerManager().delete(force=False)
    logger.info("event=argocd_delete_complete")
    return True
