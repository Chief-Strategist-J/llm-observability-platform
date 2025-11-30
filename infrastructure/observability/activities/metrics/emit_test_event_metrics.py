import logging
import time
import uuid
import asyncio
from typing import Dict, Any
from temporalio import activity
import urllib.request
import urllib.error
import json

logger = logging.getLogger(__name__)

@activity.defn
async def emit_test_event_metrics(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("emit_test_event_metrics_start params=%s", list(params.keys()))

    prometheus_url = params.get("prometheus_url", "http://prometheus-instance-0:9090")
    wait_ms = int(params.get("latency_wait_ms", 500))
    
    logger.debug("emit_test_event_metrics_params url=%s wait=%s", prometheus_url, wait_ms)

    try:
        token = f"SYNTH-{uuid.uuid4().hex}"
        timestamp = int(time.time() * 1000)
        
        metric_name = f"test_metric_{token}"
        metric_value = 42
        
        logger.info("emit_test_event_metrics_generated token=%s metric=%s value=%s", 
                   token, metric_name, metric_value)
        
        prometheus_format = f"{metric_name}{{environment=\"development\",token=\"{token}\"}} {metric_value} {timestamp}\n"
        
        logger.debug("emit_test_event_metrics_format data=%s", prometheus_format)
        
        push_url = prometheus_url.replace("/api/v1/query", "/api/v1/write")
        if not push_url.endswith("/write"):
            if "/api/v1" in push_url:
                push_url = push_url.split("/api/v1")[0] + "/api/v1/write"
            else:
                push_url = f"{push_url.rstrip('/')}/api/v1/write"
        
        logger.info("emit_test_event_metrics_push_url url=%s", push_url)
        
        try:
            req = urllib.request.Request(
                push_url,
                data=prometheus_format.encode("utf-8"),
                headers={"Content-Type": "text/plain"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.getcode()
                logger.info("emit_test_event_metrics_pushed status=%s", status)
        except urllib.error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                pass
            logger.warning("emit_test_event_metrics_push_http_error code=%s body=%s", e.code, body)
        except Exception as e:
            logger.warning("emit_test_event_metrics_push_error error=%s", e)

        await asyncio.sleep(wait_ms / 1000.0)
        await asyncio.sleep(2.0)

        logger.info("emit_test_event_metrics_complete token=%s metric=%s", token, metric_name)
        return {"success": True, "data": {"token": token, "metric_name": metric_name}, "error": None}

    except Exception as e:
        logger.exception("emit_test_event_metrics_error error=%s", e)
        return {"success": False, "data": None, "error": "emit_failed"}