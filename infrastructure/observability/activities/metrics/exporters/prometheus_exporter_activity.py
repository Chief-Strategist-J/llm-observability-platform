import logging
import time
import json
import urllib.request
import urllib.error
from typing import Dict, Any
from temporalio import activity
from infrastructure.observability.config.constants import OBSERVABILITY_CONFIG

logger = logging.getLogger(__name__)

@activity.defn
async def prometheus_exporter_activity(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Export metrics to Prometheus via remote write endpoint.
    
    Args:
        params: Dictionary containing:
            - prometheus_push_url: Prometheus push gateway or remote write URL
            - metrics: List of metric dictionaries or single metric
            - labels: Additional labels to apply to metrics
            
    Returns:
        Dictionary with success status, data, and error info
    """
    logger.info("prometheus_exporter_activity started with params keys: %s", list(params.keys()))
    prometheus_push_url = params.get("prometheus_push_url", OBSERVABILITY_CONFIG.PROMETHEUS_WRITE_URL)
    raw_metrics = params.get("metrics") or params.get("metric") or []
    if isinstance(raw_metrics, dict):
        raw_metrics = [raw_metrics]
    labels = params.get("labels", {"job": "synthetic"})

    if not raw_metrics:
        logger.error("prometheus_exporter_activity missing metrics")
        return {"success": False, "data": None, "error": "missing_metrics"}

    try:
        # Build Prometheus remote write format
        samples = []
        ts_ms = int(time.time() * 1000)
        
        for metric in raw_metrics:
            metric_name = metric.get("name", "custom_metric")
            metric_value = metric.get("value", 0)
            metric_labels = {**labels, **metric.get("labels", {})}
            
            # Create label pairs for Prometheus format
            label_pairs = [{"name": k, "value": str(v)} for k, v in metric_labels.items()]
            
            samples.append({
                "labels": label_pairs,
                "samples": [{
                    "value": float(metric_value),
                    "timestamp": ts_ms
                }]
            })

        payload = {"timeseries": samples}
        body = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            prometheus_push_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Prometheus-Remote-Write-Version": "0.1.0"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.getcode()
            resp_body = resp.read().decode("utf-8", errors="ignore")
            logger.info("prometheus_exporter_activity pushed %d metrics status=%s", len(samples), status)
            return {"success": True, "data": {"status": status, "response": resp_body, "count": len(samples)}, "error": None}

    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            body = ""
        logger.error("prometheus_exporter_activity http_error %s body=%s", getattr(e, "code", None), body)
        return {"success": False, "data": {"status": getattr(e, "code", None), "body": body}, "error": "http_error"}

    except Exception as e:
        logger.exception("prometheus_exporter_activity unexpected error: %s", e)
        return {"success": False, "data": None, "error": "unexpected_error"}
