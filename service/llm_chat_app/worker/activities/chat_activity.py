from pathlib import Path as _Path
from dotenv import load_dotenv as _load_dotenv
_load_dotenv(_Path(__file__).resolve().parents[2] / ".env.llm_chat_app", override=True)

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from temporalio import activity

from infrastructure.orchestrator.base.base_container_activity import BaseService, ContainerConfig
from infrastructure.orchestrator.activities.configurations_activity.neo4j_activity import Neo4jManager
from core.config.config import DEFAULT_IMAGE_TAG, DEFAULT_CONTAINER_NAME

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

LLM_CHAT_SKIP_DOCKER = os.environ.get("LLM_CHAT_SKIP_DOCKER", "false").lower() in ("1", "true", "yes")
LLM_CHAT_SKIP_CLOUDFLARE = os.environ.get("LLM_CHAT_SKIP_CLOUDFLARE", "false").lower() in ("1", "true", "yes")

class ChatManager(BaseService):
    SERVICE_NAME = "Chat"
    SERVICE_DESCRIPTION = "Streamlit chat application"
    DEFAULT_PORT = 8501
    IMAGE = DEFAULT_IMAGE_TAG

    def __init__(self, image: str = IMAGE, name: str = DEFAULT_CONTAINER_NAME):
        config = ContainerConfig(
            image=image,
            name=name,
            ports={"8501/tcp": 8501},
            network="data-network",
            memory="1g",
            memory_reservation="512m",
            cpus=1.0,
            restart="unless-stopped",
        )
        super().__init__(config)

    def _resolve_context(self, path: str) -> Path:
        p = Path(path)
        if not p.is_absolute():
            cur = Path(__file__).resolve().parent
            markers = ("service", "pyproject.toml", "setup.py", ".git")
            for _ in range(10):
                if any((cur / m).exists() for m in markers):
                    break
                if cur.parent == cur:
                    break
                cur = cur.parent
            p = (cur / p).resolve()
        return p

    def _find_docker_context(self, start_path: str) -> Optional[Path]:
        start = self._resolve_context(start_path)
        cur = start
        while True:
            if (cur / "Dockerfile").exists() or (cur / "dockerfile").exists():
                return cur
            if cur.parent == cur:
                break
            cur = cur.parent
        return None

    def build_image(self, path: str = ".", tag: Optional[str] = None) -> None:
        if LLM_CHAT_SKIP_DOCKER:
            logger.info("build_image: skipped because LLM_CHAT_SKIP_DOCKER=%s", os.environ.get("LLM_CHAT_SKIP_DOCKER"))
            return
        ctx = self._find_docker_context(path) or self._resolve_context(path)
        tag = tag or self.config.image
        dockerfile1 = ctx / "Dockerfile"
        dockerfile2 = ctx / "dockerfile"
        logger.info("build_image start resolved_path=%s tag=%s", str(ctx), tag)
        if not dockerfile1.exists() and not dockerfile2.exists():
            logger.error("build_image missing Dockerfile context=%s", str(ctx))
            raise FileNotFoundError(f"Dockerfile not found in {ctx}")
        import docker
        client = docker.from_env()
        try:
            image, logs = client.images.build(path=str(ctx), tag=tag, rm=True, pull=False)
            img_id = getattr(image, "id", None)
            logger.info("build_image complete tag=%s image_id=%s", tag, img_id)
            for l in logs:
                try:
                    logger.debug("build_image log=%s", l.get("stream") or l.get("status") or l)
                except Exception:
                    logger.debug("build_image raw=%s", l)
        except Exception as e:
            logger.exception("build_image failed context=%s tag=%s error=%s", str(ctx), tag, e)
            raise

    def delete_image(self, force: bool = False) -> None:
        if LLM_CHAT_SKIP_DOCKER:
            logger.info("delete_image: skipped because LLM_CHAT_SKIP_DOCKER=%s", os.environ.get("LLM_CHAT_SKIP_DOCKER"))
            return
        client = self.manager.client
        logger.info("delete_image image=%s force=%s", self.config.image, force)
        client.images.remove(self.config.image, force=force)

def _manager_name_from_params(params: Optional[Dict[str, Any]]) -> str:
    if not params:
        return DEFAULT_CONTAINER_NAME
    return params.get("name", DEFAULT_CONTAINER_NAME)

@activity.defn
async def build_chat_image_activity(params: Dict[str, Any]) -> bool:
    if LLM_CHAT_SKIP_DOCKER:
        logger.info("build_chat_image_activity: skipped")
        return True
    path = params.get("context", ".")
    tag = params.get("tag", ChatManager.IMAGE)
    manager = ChatManager(image=tag)
    try:
        manager.build_image(path=path, tag=manager.config.image)
        logger.info("build_chat_image_activity success tag=%s context=%s", manager.config.image, path)
        return True
    except FileNotFoundError:
        logger.error("build_chat_image_activity failed: Dockerfile not found. To skip docker set LLM_CHAT_SKIP_DOCKER=true or place Dockerfile in project.")
        return False
    except Exception as e:
        logger.exception("build_chat_image_activity failed tag=%s context=%s error=%s", tag, path, e)
        return False

@activity.defn
async def run_chat_container_activity(params: Dict[str, Any]) -> bool:
    if LLM_CHAT_SKIP_DOCKER:
        logger.info("run_chat_container_activity: skipped")
        return True
    image = params.get("image", ChatManager.IMAGE)
    name = _manager_name_from_params(params)
    manager = ChatManager(image=image, name=name)
    try:
        try:
            import docker
            client = docker.from_env()
            try:
                client.images.get(image)
            except Exception:
                dockerctx = manager._find_docker_context(params.get("context", "."))
                if not dockerctx:
                    logger.error("run_chat_container_activity: image %s not found locally and no Dockerfile present. Will not attempt to pull. Set LLM_CHAT_SKIP_DOCKER=true if you don't want docker operations.", image)
                    return False
        except Exception:
            pass
        manager.run()
        logger.info("run_chat_container_activity success name=%s image=%s", manager.config.name, manager.config.image)
        return True
    except Exception as e:
        logger.exception("run_chat_container_activity failed name=%s image=%s error=%s", name, image, e)
        return False

@activity.defn
async def stop_chat_container_activity(params: Dict[str, Any]) -> bool:
    if LLM_CHAT_SKIP_DOCKER:
        logger.info("stop_chat_container_activity: skipped")
        return True
    name = _manager_name_from_params(params)
    timeout = int(params.get("timeout", 30)) if params else 30
    manager = ChatManager(name=name)
    try:
        manager.stop(timeout=timeout)
        logger.info("stop_chat_container_activity success name=%s timeout=%s", manager.config.name, timeout)
        return True
    except Exception as e:
        logger.exception("stop_chat_container_activity failed name=%s error=%s", name, e)
        return False

@activity.defn
async def delete_chat_container_activity(params: Dict[str, Any]) -> bool:
    if LLM_CHAT_SKIP_DOCKER:
        logger.info("delete_chat_container_activity: skipped")
        return True
    name = _manager_name_from_params(params)
    force = bool(params.get("force", False)) if params else False
    manager = ChatManager(name=name)
    try:
        manager.delete(force=force)
        logger.info("delete_chat_container_activity success name=%s force=%s", manager.config.name, force)
        return True
    except Exception as e:
        logger.exception("delete_chat_container_activity failed name=%s error=%s", name, e)
        return False

@activity.defn
async def delete_chat_image_activity(params: Dict[str, Any]) -> bool:
    if LLM_CHAT_SKIP_DOCKER:
        logger.info("delete_chat_image_activity: skipped")
        return True
    tag = params.get("tag", ChatManager.IMAGE)
    force = bool(params.get("force", False))
    manager = ChatManager(image=tag)
    try:
        manager.delete_image(force=force)
        logger.info("delete_chat_image_activity success image=%s force=%s", manager.config.image, force)
        return True
    except Exception as e:
        logger.exception("delete_chat_image_activity failed image=%s error=%s", tag, e)
        return False

@activity.defn
async def start_neo4j_dependency_activity(params: Dict[str, Any]) -> bool:
    try:
        nm = Neo4jManager()
        nm.run()
        logger.info("start_neo4j_dependency_activity success")
        return True
    except Exception as e:
        logger.exception("start_neo4j_dependency_activity failed error=%s", e)
        return False

@activity.defn
async def stop_neo4j_dependency_activity(params: Dict[str, Any]) -> bool:
    timeout = int(params.get("timeout", 30)) if params else 30
    try:
        nm = Neo4jManager()
        nm.stop(timeout=timeout)
        logger.info("stop_neo4j_dependency_activity success timeout=%s", timeout)
        return True
    except Exception as e:
        logger.exception("stop_neo4j_dependency_activity failed error=%s", e)
        return False

@activity.defn
async def delete_neo4j_dependency_activity(params: Dict[str, Any]) -> bool:
    force = bool(params.get("force", False))
    try:
        nm = Neo4jManager()
        nm.delete(force=force)
        logger.info("delete_neo4j_dependency_activity success force=%s", force)
        return True
    except Exception as e:
        logger.exception("delete_neoj_dependency_activity failed error=%s", e)
        return False

@activity.defn
async def verify_cloudflare_dependency_activity(params: Dict[str, Any]) -> bool:
    logger.info("event=start_verification params=%s", params)

    if LLM_CHAT_SKIP_CLOUDFLARE:
        logger.info("event=skip_verification reason=flag_enabled")
        return True

    url = (
        params.get("cloudflare_url")
        or os.environ.get("CLOUDFLARE_AI_URL")
        or os.environ.get("CLOUDFLARE_AI_BASE")
    )

    token = (
        params.get("cloudflare_token")
        or os.environ.get("CLOUDFLARE_API_TOKEN")
    )

    logger.info("event=env_loaded url=%s token_present=%s", url, bool(token))

    if url and "/ai/run" in url and "@cf/" not in url:
        if not url.endswith("/"):
            url = url + "/"
        url = url + "@cf/meta/llama-3.1-8b-instruct"
        logger.info("event=url_normalized model_url=%s", url)

    if not url or not token:
        logger.error("event=missing_fields url=%s token=%s", url, token)
        return False

    verify_url = "https://api.cloudflare.com/client/v4/user/tokens/verify"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resp1 = requests.get(verify_url, headers=headers, timeout=10)
        logger.info("event=token_verify status=%s", resp1.status_code)

        payload = {"prompt": "hello"}
        resp2 = requests.post(url, headers=headers, json=payload, timeout=10)
        logger.info("event=model_test status=%s", resp2.status_code)

        ok = resp1.status_code < 400 and resp2.status_code < 400
        logger.info("event=verification_done success=%s", ok)
        return ok

    except Exception as e:
        logger.exception("event=verification_exception url=%s error=%s", url, e)
        return False


@activity.defn
async def check_chat_health_activity(params: Dict[str, Any]) -> bool:
    if LLM_CHAT_SKIP_DOCKER:
        logger.info("check_chat_health_activity: skipped because LLM_CHAT_SKIP_DOCKER=%s", os.environ.get("LLM_CHAT_SKIP_DOCKER"))
        return True
    import time
    host = params.get("host", "http://localhost:8501")
    attempts = int(params.get("attempts", 10))
    delay = float(params.get("initial_delay", 0.5))
    max_delay = float(params.get("max_delay", 5.0))
    for i in range(1, attempts + 1):
        try:
            resp = requests.get(host, timeout=5)
            logger.info("check_chat_health_activity attempt=%d status=%s host=%s", i, getattr(resp, "status_code", None), host)
            if getattr(resp, "status_code", 999) < 400:
                return True
        except Exception as e:
            logger.warning("check_chat_health_activity attempt=%d failed host=%s error=%s", i, host, e)
        sleep_for = min(max_delay, delay * (2 ** (i - 1)))
        time.sleep(sleep_for)
    logger.error("check_chat_health_activity failed host=%s after=%d attempts", host, attempts)
    return False
