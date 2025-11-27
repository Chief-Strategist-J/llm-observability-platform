import logging
from pathlib import Path
import glob
from typing import Dict, Any, List
from temporalio import activity
import yaml

logger = logging.getLogger(__name__)

@activity.defn
async def configure_source_paths_tracings(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.debug("Entered configure_source_paths_tracings with raw params: %s", params)
    logger.info("configure_source_paths_tracings started with params: %s", params)

    config_path = params.get("config_path")
    logger.debug("Resolved config_path: %s", config_path)

    if not config_path:
        logger.error("missing_config_path")
        return {"success": False, "data": None, "error": "missing_config_path"}

    try:
        logger.debug("Reading configuration file: %s", config_path)
        cfg_text = Path(config_path).read_text(encoding="utf-8")
        logger.debug("Configuration file size: %d characters", len(cfg_text))

        cfg = yaml.safe_load(cfg_text) or {}
        logger.debug("Parsed YAML configuration: %s", cfg)

        receivers = cfg.get("receivers", {}) or {}
        logger.debug("Extracted receivers section with %d entries", len(receivers))

        includes: List[str] = []

        for rcfg_key, rcfg in receivers.items():
            logger.debug("Processing receiver key=%s value=%s", rcfg_key, rcfg)

            if isinstance(rcfg, dict):
                if "include" in rcfg and isinstance(rcfg.get("include"), list):
                    logger.debug("Found include list with %d entries", len(rcfg.get("include")))
                    includes.extend(rcfg.get("include"))

                elif "otlp" in rcfg and isinstance(rcfg.get("otlp"), dict):
                    logger.debug("Found otlp receiver definition")
                    endpoints = rcfg["otlp"].get("protocols", {})
                    logger.debug("OTLP protocols section: %s", endpoints)

                    if isinstance(endpoints, dict):
                        for proto_key, proto_cfg in endpoints.items():
                            logger.debug("Processing OTLP protocol key=%s value=%s", proto_key, proto_cfg)
                            if isinstance(proto_cfg, dict):
                                endpoint = proto_cfg.get("endpoint", "")
                                logger.debug("Extracted OTLP endpoint: %s", endpoint)
                                if endpoint:
                                    includes.append(endpoint)

        logger.debug("Collected include patterns/endpoints: %s", includes)

        resolved: Dict[str, List[str]] = {}
        for pattern in includes:
            logger.debug("Resolving pattern: %s", pattern)

            if pattern.startswith("http://") or pattern.startswith("https://") or ":" in pattern:
                logger.debug("Detected endpoint (not filesystem pattern): %s", pattern)
                resolved[pattern] = [pattern]
            else:
                logger.debug("Resolving filesystem glob pattern: %s", pattern)
                matches = [str(Path(p).resolve()) for p in glob.glob(pattern)]
                logger.debug("Resolved %d filesystem paths for pattern %s", len(matches), pattern)
                resolved[pattern] = matches

        logger.info("configure_source_paths_tracings resolved %d include patterns", len(resolved))
        logger.debug("Final resolved mapping: %s", resolved)

        return {
            "success": True,
            "data": {"resolved_paths": resolved, "includes": includes},
            "error": None
        }

    except Exception as e:
        logger.debug("Unexpected exception type: %s", type(e))
        logger.exception("configure_source_paths_tracings error: %s", e)
        return {"success": False, "data": None, "error": "path_resolution_failed"}
