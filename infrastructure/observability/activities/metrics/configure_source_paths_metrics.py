import logging
from pathlib import Path
from typing import Dict, Any, List
from temporalio import activity
import yaml

logger = logging.getLogger(__name__)

@activity.defn
async def configure_source_paths_metrics(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("configure_source_paths_metrics_start params=%s", list(params.keys()))
    config_path = params.get("config_path")
    if not config_path:
        logger.error("configure_source_paths_metrics_missing_config_path")
        return {"success": False, "data": None, "error": "missing_config_path"}

    try:
        cfg_text = Path(config_path).read_text(encoding="utf-8")
        cfg = yaml.safe_load(cfg_text) or {}
        receivers = cfg.get("receivers", {}) or {}
        
        logger.debug("configure_source_paths_metrics_receivers count=%s", len(receivers))

        endpoints: List[str] = []
        for rcvr_name, rcvr_config in receivers.items():
            logger.debug("configure_source_paths_metrics_receiver name=%s", rcvr_name)
            if isinstance(rcvr_config, dict):
                if rcvr_name == "prometheus":
                    scrape_configs = rcvr_config.get("config", {}).get("scrape_configs", [])
                    for sc in scrape_configs:
                        job_name = sc.get("job_name", "unknown")
                        static_configs = sc.get("static_configs", [])
                        for static in static_configs:
                            targets = static.get("targets", [])
                            endpoints.extend(targets)
                            logger.debug("configure_source_paths_metrics_targets job=%s targets=%s", 
                                       job_name, targets)

        resolved: Dict[str, List[str]] = {
            "prometheus_endpoints": endpoints
        }

        logger.info("configure_source_paths_metrics_resolved endpoints=%s", len(endpoints))
        return {"success": True, "data": {"resolved_paths": resolved, "endpoints": endpoints}, "error": None}
    except Exception as e:
        logger.exception("configure_source_paths_metrics_error error=%s", e)
        return {"success": False, "data": None, "error": "path_resolution_failed"}