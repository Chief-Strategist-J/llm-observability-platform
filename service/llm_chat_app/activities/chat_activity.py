import os
import logging
from typing import Dict, Any, Optional
import requests
from temporalio import activity
from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.activities.configurations_activity.neo4j_activity import Neo4jManager
from config.config import DEFAULT_IMAGE_TAG, DEFAULT_CONTAINER_NAME
logger = logging.getLogger(__name__)

class ChatManager(BaseService):
    SERVICE_NAME = "Chat"
    SERVICE_DESCRIPTION = "Streamlit chat application"
    DEFAULT_PORT = 8501
    IMAGE = DEFAULT_IMAGE_TAG

    def __init__(self, image: str = IMAGE, name: str = DEFAULT_CONTAINER_NAME):
        config = ContainerConfig(image=image, name=name, ports={8501: 8501}, network="data-network", memory="1g", memory_reservation="512m", cpus=1.0, restart="unless-stopped")
        super().__init__(config)

    def build_image(self, path: str = ".", tag: Optional[str] = None) -> None:
        import docker
        tag = tag or self.config.image
        client = docker.from_env()
        logger.info("docker build start path=%s tag=%s", path, tag)
        image, logs = client.images.build(path=path, tag=tag, rm=True)
        logger.info("docker build complete image_id=%s", getattr(image, "id", None))
        return

    def delete_image(self, force: bool = False) -> None:
        client = self.manager.client
        logger.info("docker image remove image=%s force=%s", self.config.image, force)
        client.images.remove(self.config.image, force=force)

@activity.defn
async def build_chat_image_activity(params: Dict[str, Any]) -> bool:
    manager = ChatManager(image=params.get("tag", ChatManager.IMAGE))
    path = params.get("context", ".")
    try:
        manager.build_image(path=path, tag=manager.config.image)
        logger.info("build_chat_image_activity succeeded tag=%s path=%s", manager.config.image, path)
        return True
    except Exception:
        logger.exception("build_chat_image_activity failed")
        return False

@activity.defn
async def run_chat_container_activity(params: Dict[str, Any]) -> bool:
    manager = ChatManager(image=params.get("image", ChatManager.IMAGE), name=params.get("name", manager_name(params=None)))
    try:
        manager.run()
        logger.info("run_chat_container_activity started container=%s image=%s", manager.config.name, manager.config.image)
        return True
    except Exception:
        logger.exception("run_chat_container_activity failed")
        return False

def manager_name(params: Optional[Dict[str, Any]]):
    if not params:
        return DEFAULT_CONTAINER_NAME
    return params.get("name", DEFAULT_CONTAINER_NAME)

@activity.defn
async def stop_chat_container_activity(params: Dict[str, Any]) -> bool:
    manager = ChatManager(name=manager_name(params))
    try:
        timeout = int(params.get("timeout", 30)) if params else 30
        manager.stop(timeout=timeout)
        logger.info("stop_chat_container_activity stopped name=%s", manager.config.name)
        return True
    except Exception:
        logger.exception("stop_chat_container_activity failed")
        return False

@activity.defn
async def delete_chat_container_activity(params: Dict[str, Any]) -> bool:
    manager = ChatManager(name=manager_name(params))
    try:
        force = bool(params.get("force", False)) if params else False
        manager.delete(force=force)
        logger.info("delete_chat_container_activity deleted name=%s force=%s", manager.config.name, force)
        return True
    except Exception:
        logger.exception("delete_chat_container_activity failed")
        return False

@activity.defn
async def delete_chat_image_activity(params: Dict[str, Any]) -> bool:
    manager = ChatManager(image=params.get("tag", ChatManager.IMAGE))
    try:
        force = bool(params.get("force", False))
        manager.delete_image(force=force)
        logger.info("delete_chat_image_activity removed image=%s force=%s", manager.config.image, force)
        return True
    except Exception:
        logger.exception("delete_chat_image_activity failed")
        return False

@activity.defn
async def start_neo4j_dependency_activity(params: Dict[str, Any]) -> bool:
    try:
        nm = Neo4jManager()
        nm.run()
        logger.info("start_neo4j_dependency_activity started neo4j container")
        return True
    except Exception:
        logger.exception("start_neo4j_dependency_activity failed")
        return False

@activity.defn
async def stop_neo4j_dependency_activity(params: Dict[str, Any]) -> bool:
    try:
        nm = Neo4jManager()
        nm.stop(timeout=int(params.get("timeout", 30)) if params else 30)
        logger.info("stop_neo4j_dependency_activity stopped neo4j")
        return True
    except Exception:
        logger.exception("stop_neo4j_dependency_activity failed")
        return False

@activity.defn
async def delete_neo4j_dependency_activity(params: Dict[str, Any]) -> bool:
    try:
        nm = Neo4jManager()
        nm.delete(force=bool(params.get("force", False)))
        logger.info("delete_neo4j_dependency_activity deleted neo4j")
        return True
    except Exception:
        logger.exception("delete_neo4j_dependency_activity failed")
        return False

@activity.defn
async def verify_cloudflare_dependency_activity(params: Dict[str, Any]) -> bool:
    url = params.get("cloudflare_url") or os.environ.get("CLOUDFLARE_AI_URL")
    token = params.get("cloudflare_token") or os.environ.get("CLOUDFLARE_API_TOKEN")
    if not url or not token:
        logger.error("verify_cloudflare_dependency_activity missing url/token")
        return False
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.head(url, headers=headers, timeout=10)
        logger.info("verify_cloudflare_dependency_activity status=%s url=%s", resp.status_code, url)
        return resp.status_code < 400
    except Exception:
        logger.exception("verify_cloudflare_dependency_activity failed")
        return False

@activity.defn
async def check_chat_health_activity(params: Dict[str, Any]) -> bool:
    host = params.get("host", "http://localhost:8501")
    try:
        resp = requests.get(host, timeout=10)
        logger.info("check_chat_health_activity status=%s host=%s", resp.status_code, host)
        return resp.status_code < 400
    except Exception:
        logger.exception("check_chat_health_activity failed")
        return False
