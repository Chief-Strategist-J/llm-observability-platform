import logging
from pathlib import Path
from datetime import datetime
import yaml
import time
from temporalio import activity
from urllib.request import urlopen, URLError
from infrastructure.orchestrator.activities.configurations_activity.opentelemetry_collector import OpenTelemetryCollectorManager

logger = logging.getLogger(__name__)

@activity.defn(name="application_stdout_configure_activity")
async def application_stdout_configure_activity(params: dict) -> dict:
    dynamic_dir = Path("/home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/dynamicconfig")
    logs_dir = dynamic_dir / "logs"
    config_path = dynamic_dir / "base.yaml"

    dynamic_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    for d in [dynamic_dir, logs_dir]:
        try:
            d.chmod(0o777)
        except Exception:
            pass

    log_file = logs_dir / "otel-logs.jsonl"
    if log_file.exists():
        try:
            log_file.unlink()
        except Exception:
            pass
    log_file.touch(exist_ok=True)
    try:
        log_file.chmod(0o666)
    except Exception:
        pass

    labels = params.get("labels", {"app": "application-stdout-ingest", "environment": "development"})
    batch_size = int(params.get("batch_size", 100))
    flush = int(params.get("flush_interval_seconds", 5))
    host_loki_port = int(params.get("host_loki_port", 31002))
    loki_endpoint = f"http://host.docker.internal:{host_loki_port}/loki/api/v1/push"

    config = {
        "receivers": {
            "otlp": {
                "protocols": {
                    "grpc": {"endpoint": "0.0.0.0:4317"},
                    "http": {"endpoint": "0.0.0.0:4318"}
                }
            }
        },
        "processors": {
            "batch": {"send_batch_size": batch_size, "timeout": f"{flush}s"},
            "memory_limiter": {"check_interval": "1s", "limit_mib": 128},
            "resource": {"attributes": [{"key": k, "value": v, "action": "upsert"} for k, v in labels.items()]}
        },
        "exporters": {
            "debug": {"verbosity": "detailed"},
            "file": {"path": "/var/log/otelcol/otel-logs.jsonl"},
            "loki": {"endpoint": loki_endpoint}
        },
        "extensions": {"health_check": {"endpoint": "0.0.0.0:13133"}},
        "service": {
            "extensions": ["health_check"],
            "pipelines": {
                "logs": {
                    "receivers": ["otlp"],
                    "processors": ["memory_limiter", "resource", "batch"],
                    "exporters": ["loki", "file", "debug"]
                }
            }
        }
    }

    with config_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, sort_keys=False)

    logger.info("wrote config to %s", str(config_path))

    mgr = OpenTelemetryCollectorManager()
    time.sleep(2)
    mgr.safe_restart()

    collector_ready = False
    loki_ready = False

    health_url = "http://localhost:13133/"
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            resp = urlopen(health_url, timeout=2)
            if getattr(resp, "status", None) in (200, None):
                collector_ready = True
                break
        except Exception:
            pass
        time.sleep(1)

    if collector_ready:
        loki_health = f"http://localhost:{host_loki_port}/ready"
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                resp = urlopen(loki_health, timeout=2)
                if getattr(resp, "status", None) in (200, None):
                    loki_ready = True
                    break
            except Exception:
                pass
            time.sleep(1)

    result = {
        "config_path": str(config_path),
        "labels": dict(labels),
        "batch_size": batch_size,
        "flush_interval_seconds": flush,
        "loki_endpoint": loki_endpoint,
        "collector_ready": collector_ready,
        "loki_ready": loki_ready,
        "written_at": datetime.utcnow().isoformat() + "Z",
    }

    logger.info("config complete: collector_ready=%s loki_ready=%s", collector_ready, loki_ready)
    return result

