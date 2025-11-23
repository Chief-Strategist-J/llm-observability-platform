import logging
import time
import uuid
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from temporalio import activity
import yaml

logger = logging.getLogger(__name__)

@activity.defn
async def emit_test_event_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("emit_test_event_logs started with params: %s", params)

    config_path = params.get("config_path")
    message = params.get("message")
    wait_ms = int(params.get("latency_wait_ms", 500))
    host_mount_dir_param: Optional[str] = params.get("host_mount_dir")

    if not config_path:
        logger.error("emit_test_event_logs missing_config_path")
        return {"success": False, "data": None, "error": "missing_config_path"}

    try:
        cfg_text = Path(config_path).read_text(encoding="utf-8")
        cfg = yaml.safe_load(cfg_text) or {}
        receivers = cfg.get("receivers", {})

        include_patterns: List[str] = []
        for rcvr_name, rcvr_config in receivers.items():
            if isinstance(rcvr_config, dict):
                inc = rcvr_config.get("include")
                if isinstance(inc, list):
                    include_patterns.extend(inc)
                    continue
                filelog_cfg = rcvr_config.get("filelog")
                if isinstance(filelog_cfg, dict):
                    inc2 = filelog_cfg.get("include", [])
                    if isinstance(inc2, list):
                        include_patterns.extend(inc2)

        if not include_patterns:
            logger.error("emit_test_event_logs no_include_patterns found")
            return {"success": False, "data": None, "error": "no_include_patterns"}

        if host_mount_dir_param:
            host_mount_dir = Path(host_mount_dir_param).resolve()
        else:
            try:
                host_mount_dir = Path(config_path).resolve().parent
            except Exception:
                host_mount_dir = Path.cwd().resolve()

        if not host_mount_dir.exists():
            try:
                host_mount_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                logger.debug("Could not create host_mount_dir: %s", host_mount_dir)

        token = f"SYNTH-{uuid.uuid4().hex}"
        line = message or f'{{"synth_token":"{token}","ts":{int(time.time())},"level":"info","service":"test"}}'

        appended_to: List[str] = []

        for pattern in include_patterns:
            try:
                if isinstance(pattern, bytes):
                    pattern = pattern.decode("utf-8", errors="ignore")

                pattern_str = str(pattern).strip()

                if pattern_str.startswith("/etc/otelcol"):
                    rel = pattern_str[len("/etc/otelcol") :].lstrip("/")
                    target_file = (host_mount_dir / rel).resolve()
                else:
                    target_file = Path(pattern_str).resolve()

                target_file.parent.mkdir(parents=True, exist_ok=True)

                if not target_file.exists():
                    target_file.write_text("", encoding="utf-8")
                    try:
                        target_file.chmod(0o666)
                    except Exception:
                        logger.debug("Could not chmod %s", target_file)

                with target_file.open("a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
                    fh.flush()
                    try:
                        os.fsync(fh.fileno())
                    except Exception:
                        logger.debug("fsync failed for %s", target_file)

                appended_to.append(str(target_file))

            except Exception as e:
                logger.exception("emit_test_event_logs failed writing to %s: %s", pattern, e)

        if not appended_to:
            logger.error("emit_test_event_logs no_files_written")
            return {"success": False, "data": None, "error": "no_files_written"}

        await asyncio.sleep(wait_ms / 1000.0)
        await asyncio.sleep(2.0)

        logger.info("emit_test_event_logs completed token=%s files=%s", token, appended_to)
        return {"success": True, "data": {"token": token, "appended_to": appended_to}, "error": None}

    except Exception as e:
        logger.exception("emit_test_event_logs error: %s", e)
        return {"success": False, "data": None, "error": "emit_failed"}
