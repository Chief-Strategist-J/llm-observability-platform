import logging
from typing import Dict, Any, List, Optional
from temporalio import activity
from infrastructure.observability_platform.ingest.application_stdout.model.config_model import FileConfigStore
import os
logger = logging.getLogger(__name__)
CONFIG_PATH = "infrastructure/observability_platform/ingest/config/log_discovery_config.yaml"
try:
    import docker
    from docker.errors import DockerException
    DOCKER_AVAILABLE = True
except Exception:
    docker = None
    DockerException = Exception
    DOCKER_AVAILABLE = False

class DefaultLabelEnricher:
    TAG = "label.enricher"
    def __init__(self):
        self.store = FileConfigStore(CONFIG_PATH)
        self.docker_client = None
        if DOCKER_AVAILABLE:
            try:
                client = docker.from_env()
                client.ping()
                self.docker_client = client
                logger.info("%s docker client connected via environment", self.TAG)
            except DockerException:
                try:
                    self.docker_client = docker.DockerClient(base_url="tcp://127.0.0.1:2375")
                    self.docker_client.ping()
                    logger.info("%s docker client connected via tcp://127.0.0.1:2375", self.TAG)
                except DockerException:
                    self.docker_client = None
                    logger.info("%s docker client unavailable", self.TAG)
        else:
            logger.info("%s docker SDK not installed; skipping container metadata enrichment", self.TAG)

    def _resolve_labels(self, labels: Optional[Dict[str, str]]) -> Dict[str, str]:
        if labels is not None:
            return dict(labels)
        cfg = self.store.load()
        return dict(getattr(cfg.labels, "values", {}))

    def enrich(self, files: List[str], labels: Optional[Dict[str, str]]) -> List[Dict[str, Any]]:
        resolved = self._resolve_labels(labels)
        container_map: Dict[str, Dict[str, Any]] = {}
        if self.docker_client:
            try:
                containers = self.docker_client.containers.list(all=True)
                for c in containers:
                    try:
                        log_path = c.attrs.get("LogPath")
                        if not log_path:
                            continue
                        real = os.path.realpath(log_path)
                        container_map[log_path] = {"container": c, "real": log_path}
                        container_map[real] = {"container": c, "real": real}
                    except Exception:
                        continue
                logger.info("%s built container index count=%d", self.TAG, len(containers))
            except DockerException as e:
                logger.warning("%s cannot list containers: %s", self.TAG, str(e))
        results: List[Dict[str, Any]] = []
        for p in files:
            try:
                path = p
                final_labels = dict(resolved)
                matched = None
                if path in container_map:
                    matched = container_map[path]["container"]
                else:
                    realp = os.path.realpath(path)
                    if realp in container_map:
                        matched = container_map[realp]["container"]
                    else:
                        for key in container_map.keys():
                            if key and key in path:
                                matched = container_map[key]["container"]
                                break
                if matched:
                    try:
                        cid = getattr(matched, "id", None) or matched.attrs.get("Id")
                    except Exception:
                        cid = None
                    try:
                        name = getattr(matched, "name", None) or (matched.attrs.get("Name") or "").lstrip("/")
                    except Exception:
                        name = None
                    try:
                        image = getattr(matched, "image", None)
                        image_tag = None
                        if image:
                            try:
                                tags = getattr(image, "tags", None)
                                if tags:
                                    image_tag = tags[0]
                            except Exception:
                                image_tag = None
                        if not image_tag:
                            image_tag = matched.attrs.get("Config", {}).get("Image")
                    except Exception:
                        image_tag = None
                    if cid and "container_id" not in final_labels:
                        final_labels["container_id"] = cid
                    if name and "container_name" not in final_labels:
                        final_labels["container_name"] = name
                    if image_tag and "container_image" not in final_labels:
                        final_labels["container_image"] = image_tag
                    try:
                        docker_labels = matched.attrs.get("Config", {}).get("Labels", {}) or {}
                        for k, v in docker_labels.items():
                            key = f"docker_label_{k}"
                            if key not in final_labels:
                                final_labels[key] = v
                    except Exception:
                        pass
                    custom_name = final_labels.get("custom_name") or final_labels.get("service") or (f"{name}:{image_tag}" if name or image_tag else None)
                    if custom_name and "custom_name" not in final_labels:
                        final_labels["custom_name"] = custom_name
                    logger.info("%s enriched path=%s with container id=%s name=%s", self.TAG, path, cid, name)
                results.append({"path": path, "labels": final_labels})
            except Exception as e:
                logger.error("%s failed enriching path=%s error=%s", self.TAG, p, e, exc_info=False)
                results.append({"path": p, "labels": dict(resolved)})
        return results

@activity.defn
async def label_enrichment_activity(params: dict) -> List[Dict[str, Any]]:
    logger.info("label_enrichment_activity start")
    files = params.get("files")
    labels = params.get("labels")
    if not isinstance(files, list) or any(not isinstance(x, str) for x in files):
        logger.error("files must be List[str]")
        raise ValueError("files must be List[str]")
    enricher = DefaultLabelEnricher()
    enriched = enricher.enrich(files, labels)
    logger.info("label_enrichment_activity done count=%d", len(enriched))
    return enriched
