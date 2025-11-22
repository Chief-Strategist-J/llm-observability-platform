# infrastructure/observability/activities/log/emit_test_event_logs.py
import logging
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List
from temporalio import activity
import yaml
import glob
import os
import docker
import shlex

logger = logging.getLogger(__name__)

@activity.defn
async def emit_test_event_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("emit_test_event_logs started with params: %s", params)
    config_path = params.get("config_path")
    message = params.get("message")
    wait_ms = int(params.get("latency_wait_ms", 500))
    if not config_path:
        logger.error("missing_config_path")
        return {"success": False, "data": None, "error": "missing_config_path"}
    try:
        cfg_text = Path(config_path).read_text(encoding="utf-8")
        cfg = yaml.safe_load(cfg_text) or {}
        receivers = cfg.get("receivers", {})
        include_patterns: List[str] = []
        for rcvr in receivers.values():
            filelog_block = rcvr.get("filelog")
            if filelog_block and isinstance(filelog_block, dict):
                inc = filelog_block.get("include")
                if isinstance(inc, list):
                    include_patterns.extend(inc)
        expanded_files: List[str] = []
        for pattern in include_patterns:
            for fp in glob.glob(pattern):
                if os.path.isfile(fp):
                    expanded_files.append(fp)
        token = f"SYNTH-{uuid.uuid4().hex}"
        line = message or f'{{"synth_token":"{token}","ts":{int(time.time())}}}'
        appended_to: List[str] = []
        if expanded_files:
            for fp in expanded_files:
                try:
                    p = Path(fp)
                    with p.open("a", encoding="utf-8") as fh:
                        fh.write(line + "\n")
                    appended_to.append(fp)
                    logger.info("emit_test_event_logs appended line to %s", fp)
                except Exception as e:
                    logger.error("append_failed %s: %s", fp, str(e))
            time.sleep(wait_ms / 1000)
            return {"success": True, "data": {"token": token, "appended_to": appended_to, "count": len(appended_to)}, "error": None}
        try:
            client = docker.from_env()
        except Exception as e:
            logger.error("docker_client_error: %s", str(e))
            return {"success": False, "data": None, "error": "docker_client_error"}
        containers = client.containers.list(all=True)
        exec_ok: List[str] = []
        for c in containers:
            try:
                c.reload()
                if c.status != "running":
                    logger.info("skipping_container_not_running: %s", c.id)
                    continue
                safe_line = shlex.quote(line)
                try:
                    cmd = ["/bin/sh", "-c", f"echo {safe_line} >> /proc/1/fd/1"]
                    exec_res = c.exec_run(cmd, stdout=True, stderr=True, demux=False, user=None)
                    exit_code = exec_res.exit_code if hasattr(exec_res, "exit_code") else 0
                    if exit_code == 0:
                        exec_ok.append(c.id)
                        logger.info("emit_test_event_logs exec echo to container %s", c.id)
                    else:
                        logger.error("docker_exec_nonzero %s: code=%s", c.id, exit_code)
                except Exception:
                    try:
                        cmd = ["/bin/sh", "-c", f"printf %s\\n {safe_line} >> /proc/1/fd/1"]
                        c.exec_run(cmd)
                        exec_ok.append(c.id)
                        logger.info("emit_test_event_logs exec fallback to container %s", c.id)
                    except Exception as e:
                        logger.error("docker_exec_failed %s: %s", c.id, str(e))
            except Exception as e:
                logger.error("inspect_container_failed %s: %s", getattr(c, "id", "unknown"), str(e))
        time.sleep(wait_ms / 1000)
        return {"success": True, "data": {"token": token, "exec_ok": exec_ok, "count": len(exec_ok)}, "error": None}
    except Exception as e:
        logger.error("emit_test_event_logs error: %s", str(e))
        return {"success": False, "data": None, "error": "emit_failed"}
