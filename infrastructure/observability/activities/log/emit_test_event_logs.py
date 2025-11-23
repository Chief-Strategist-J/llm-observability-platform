import logging
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List
from temporalio import activity
import yaml

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
        logger.info("emit_test_event_logs config_text length: %d", len(cfg_text))
        
        cfg = yaml.safe_load(cfg_text) or {}
        receivers = cfg.get("receivers", {})
<<<<<<< HEAD
        
        logger.info("emit_test_event_logs receivers keys: %s", list(receivers.keys()))
=======
>>>>>>> dcbfd98fbef16d9d913e8e94ea82905b860c2c85

        include_patterns: List[str] = []
        for rcvr_name, rcvr_config in receivers.items():
            logger.info("emit_test_event_logs processing receiver: %s type=%s", rcvr_name, type(rcvr_config))
            
            if isinstance(rcvr_config, dict):
                inc = rcvr_config.get("include")
                if isinstance(inc, list):
                    include_patterns.extend(inc)
<<<<<<< HEAD
                    logger.info("emit_test_event_logs found include at top level: %s", inc)

        if not include_patterns:
            logger.error("no_include_patterns found in config, receivers=%s", receivers)
            return {"success": False, "data": None, "error": "no_include_patterns"}

        logger.info("emit_test_event_logs found patterns: %s", include_patterns)

        token = f"SYNTH-{uuid.uuid4().hex}"
        line = message or f'{{"synth_token":"{token}","ts":{int(time.time())},"level":"info","service":"test"}}'

        appended_to = []

        for pattern in include_patterns:
            logger.info("emit_test_event_logs processing pattern: %s", pattern)
            
            try:
                target_file = Path(pattern)
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                if not target_file.exists():
                    target_file.touch()
                    logger.info("emit_test_event_logs created file: %s", target_file)
                
                with target_file.open("a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
                    fh.flush()
                
                appended_to.append(str(target_file))
                logger.info("emit_test_event_logs appended to file: %s", target_file)
                
                actual_size = target_file.stat().st_size
                logger.info("emit_test_event_logs file size after write: %s bytes", actual_size)
                
            except Exception as e:
                logger.error("emit_test_event_logs failed for pattern %s: %s", pattern, str(e))

        if not appended_to:
            logger.error("emit_test_event_logs no files written")
            return {"success": False, "data": None, "error": "no_files_written"}

        logger.info("emit_test_event_logs waiting %dms for ingestion", wait_ms)
        time.sleep(wait_ms / 1000)
        
        logger.info("emit_test_event_logs additional 3s wait for otel processing")
        time.sleep(3)

        return {
            "success": True,
            "data": {"token": token, "appended_to": appended_to, "count": len(appended_to), "line": line},
=======

        if not include_patterns:
            return {"success": False, "data": None, "error": "no_include_patterns"}

        token = f"SYNTH-{uuid.uuid4().hex}"
        line = message or f'{{"synth_token":"{token}","ts":{int(time.time())}}}'

        docker_client = None
        if any(p.startswith("docker://") for p in include_patterns):
            try:
                docker_client = docker.from_env()
            except Exception as e:
                logger.error("docker_client_error %s", str(e))
                return {"success": False, "data": None, "error": "docker_client_error"}

        appended_to = []

        for pattern in include_patterns:
            if pattern.startswith("docker://"):
                raw = pattern[len("docker://"):]
                parts = raw.split("/", 1)
                if len(parts) != 2:
                    continue
                container_id, path_inside = parts
                path_inside = "/" + path_inside

                try:
                    c = docker_client.containers.get(container_id)
                    c.reload()
                    if c.status != "running":
                        continue
                    safe_line = shlex.quote(line)
                    cmd = ["/bin/sh", "-c", f"echo {safe_line} >> {path_inside}"]
                    res = c.exec_run(cmd)
                    code = res.exit_code
                    if code == 0:
                        appended_to.append(f"{container_id}:{path_inside}")
                        logger.info("emit_test_event_logs appended container %s -> %s", container_id, path_inside)
                except Exception as e:
                    logger.error("append_container_failed %s: %s", container_id, str(e))

            else:
                for fp in glob.glob(pattern):
                    if os.path.isfile(fp):
                        try:
                            p = Path(fp)
                            with p.open("a", encoding="utf-8") as fh:
                                fh.write(line + "\n")
                            appended_to.append(fp)
                            logger.info("emit_test_event_logs appended host %s", fp)
                        except Exception as e:
                            logger.error("append_host_failed %s: %s", fp, str(e))

        time.sleep(wait_ms / 1000)

        return {
            "success": True,
            "data": {"token": token, "appended_to": appended_to, "count": len(appended_to)},
>>>>>>> dcbfd98fbef16d9d913e8e94ea82905b860c2c85
            "error": None,
        }

    except Exception as e:
        logger.error("emit_test_event_logs error: %s", str(e))
        return {"success": False, "data": None, "error": "emit_failed"}