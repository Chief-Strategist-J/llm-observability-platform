import logging
from pathlib import Path
from typing import Dict, Any
from temporalio import activity
import yaml

logger = logging.getLogger(__name__)

@activity.defn
async def generate_config_metrics(params: Dict[str, Any]) -> Dict[str, Any]:
    logger.info("generate_config_metrics_start params=%s", list(params.keys()))

    dynamic_dir = Path(params.get("dynamic_dir", "/home/j/live/dinesh/llm-chatbot-python/infrastructure/orchestrator/dynamicconfig"))
    dynamic_dir.mkdir(parents=True, exist_ok=True)
    logger.debug("generate_config_metrics_dir dir=%s", dynamic_dir)

    config_file = dynamic_dir / "otel-collector-metrics.yaml"
    
    prometheus_url = params.get("prometheus_url", "http://localhost:9090")
    scrape_interval = params.get("scrape_interval", "15s")
    
    logger.info("generate_config_metrics_params prometheus_url=%s scrape_interval=%s", 
                prometheus_url, scrape_interval)
    
    internal_prometheus_url = "http://prometheus-development:9090/api/v1/write"
    logger.info("generate_config_metrics_internal_url url=%s", internal_prometheus_url)
    
    config = {
        "receivers": {
            "prometheus": {
                "config": {
                    "scrape_configs": [
                        {
                            "job_name": "otel-collector",
                            "scrape_interval": scrape_interval,
                            "static_configs": [
                                {
                                    "targets": ["localhost:8888"]
                                }
                            ]
                        },
                        {
                            "job_name": "docker-containers",
                            "scrape_interval": scrape_interval,
                            "docker_sd_configs": [
                                {
                                    "host": "unix:///var/run/docker.sock",
                                    "port": 8080
                                }
                            ],
                            "relabel_configs": [
                                {
                                    "source_labels": ["__meta_docker_container_name"],
                                    "target_label": "container_name"
                                },
                                {
                                    "source_labels": ["__meta_docker_container_id"],
                                    "target_label": "container_id"
                                }
                            ]
                        }
                    ]
                }
            },
            "hostmetrics": {
                "collection_interval": scrape_interval,
                "scrapers": {
                    "cpu": {},
                    "disk": {},
                    "filesystem": {},
                    "load": {},
                    "memory": {},
                    "network": {},
                    "process": {}
                }
            }
        },
        "processors": {
            "batch": {
                "timeout": "10s",
                "send_batch_size": 100
            },
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": "metrics-pipeline", "action": "upsert"}
                ]
            },
            "metricstransform": {
                "transforms": [
                    {
                        "include": ".*",
                        "match_type": "regexp",
                        "action": "update",
                        "operations": [
                            {
                                "action": "add_label",
                                "new_label": "environment",
                                "new_value": "development"
                            }
                        ]
                    }
                ]
            }
        },
        "exporters": {
            "prometheusremotewrite": {
                "endpoint": internal_prometheus_url,
                "tls": {
                    "insecure": True
                }
            },
            "logging": {
                "loglevel": "debug"
            }
        },
        "service": {
            "pipelines": {
                "metrics": {
                    "receivers": ["prometheus", "hostmetrics"],
                    "processors": ["resource", "metricstransform", "batch"],
                    "exporters": ["prometheusremotewrite", "logging"]
                }
            },
            "telemetry": {"logs": {"level": "info"}}
        }
    }

    try:
        with config_file.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(config, fh, default_flow_style=False, sort_keys=False)
        logger.info("generate_config_metrics_success file=%s", config_file)
        return {
            "success": True,
            "data": {"config_path": str(config_file)},
            "error": None
        }
    except Exception as e:
        logger.exception("generate_config_metrics_failed error=%s", e)
        return {"success": False, "data": None, "error": "generate_failed"}