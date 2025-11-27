import logging
from pathlib import Path
from typing import Dict, Any
from temporalio import activity
import yaml

logger = logging.getLogger(__name__)

@activity.defn
async def deploy_processor_tracings(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(
        "deploy_processor_tracings started params_keys=%s dynamic_dir=%s config_name=%s",
        list(params.keys()),
        params.get("dynamic_dir", "/etc/otelcol/generated"),
        params.get("config_name", "otel-collector-tracings-generated.yaml")
    )

    dynamic_dir = Path(params.get("dynamic_dir", "/etc/otelcol/generated"))
    config_name = params.get("config_name", "otel-collector-tracings-generated.yaml")

    try:
        cfg_file = dynamic_dir / config_name
        logger.debug("checking_config_file path=%s exists=%s", cfg_file, cfg_file.exists())

        if not cfg_file.exists():
            logger.error("deploy_processor_tracings_error error=config_not_found path=%s", str(cfg_file))
            return {"success": False, "data": None, "error": "config_not_found"}

        text = cfg_file.read_text(encoding="utf-8")
        logger.debug("config_read_success path=%s size=%d", cfg_file, len(text))

        try:
            cfg = yaml.safe_load(text) or {}
            logger.debug("yaml_parse_success processors_key_present=%s", "processors" in cfg)
        except Exception as e:
            cfg = {}
            logger.warning("yaml_parse_failed path=%s error=%s", cfg_file, e)

        processors_deployed = bool(cfg.get("processors"))
        logger.info(
            "deploy_processor_tracings processors_present=%s path=%s",
            processors_deployed,
            str(cfg_file)
        )

        return {
            "success": True,
            "data": {"processors_present": processors_deployed, "config_path": str(cfg_file)},
            "error": None
        }

    except Exception as e:
        logger.exception("deploy_processor_tracings_failure error=deploy_failed exception=%s", e)
        return {"success": False, "data": None, "error": "deploy_failed"}
