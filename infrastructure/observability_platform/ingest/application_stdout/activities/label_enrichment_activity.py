import logging
from typing import Dict, Any, List, Optional
from temporalio import activity
from infrastructure.observability_platform.ingest.application_stdout.model.config_model import FileConfigStore

logger = logging.getLogger(__name__)

CONFIG_PATH = "infrastructure/observability_platform/ingest/config/log_discovery_config.yaml"


class DefaultLabelEnricher:
    def __init__(self):
        self.store = FileConfigStore(CONFIG_PATH)

    def _resolve_labels(self, labels: Optional[Dict[str, str]]) -> Dict[str, str]:
        if labels is not None:
            return dict(labels)
        cfg = self.store.load()
        return dict(getattr(cfg.labels, "values", {}))

    def enrich(self, files: List[str], labels: Optional[Dict[str, str]]) -> List[Dict[str, Any]]:
        resolved = self._resolve_labels(labels)
        return [{"path": p, "labels": resolved} for p in files]


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
