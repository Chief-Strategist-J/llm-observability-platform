import logging
import os
from pathlib import Path

from temporalio import activity

# Configuration paths
CONFIG_DIR = "/home/j/live/dinesh/llm-chatbot-python/infrastructure/observability_platform/config"
TELEMETRY_CONFIG = os.path.join(CONFIG_DIR, "telemetry.yaml")
RECEIVERS_CONFIG = os.path.join(CONFIG_DIR, "receivers.yaml")
PROCESSORS_CONFIG = os.path.join(CONFIG_DIR, "processors.yaml")
EXPORTERS_CONFIG = os.path.join(CONFIG_DIR, "exporters.yaml")

logging.basicConfig(level=logging.INFO)

# Default configurations for OpenTelemetry Collector
DEFAULT_TELEMETRY_CONFIG = """extensions:
  health_check:
    endpoint: 0.0.0.0:13133
  memory_ballast:
    size_mib: 165

service:
  extensions: [health_check, memory_ballast]
  telemetry:
    logs:
      level: info
  pipelines:
    traces:
      receivers: [otlp]
      processors: [resource_detection, attributes, batch]
      exporters: [logging, otlp]
    metrics:
      receivers: [otlp, hostmetrics, docker_stats, prometheus]
      processors: [resource_detection, attributes, batch]
      exporters: [logging, prometheus]
    logs:
      receivers: [otlp, filelog]
      processors: [resource_detection, attributes, batch]
      exporters: [logging, loki]"""

DEFAULT_RECEIVERS_CONFIG = r"""otlp:
  protocols:
    grpc:
      endpoint: 0.0.0.0:4317
    http:
      endpoint: 0.0.0.0:4318

filelog:
  include: [/var/log/application/*.log, /var/log/infrastructure/*.log]
  start_at: beginning
  operators:
    - type: regex_parser
      regex: '^(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(?P<level>\w+)\] (?P<message>.*)$'
      timestamp:
        parse_from: attributes.time
        layout: '%Y-%m-%d %H:%M:%S'
      severity:
        parse_from: attributes.level
        mapping:
          DEBUG: 1
          INFO: 9
          WARN: 13
          WARNING: 13
          ERROR: 17

hostmetrics:
  collection_interval: 30s
  scrapers:
    cpu:
    disk:
    memory:
    network:

docker_stats:
  collection_interval: 30s
  endpoint: unix:///var/run/docker.sock

prometheus:
  config:
    scrape_configs:
      - job_name: 'otel-collector'
        static_configs:
          - targets: ['localhost:8888']
        scrape_interval: 30s"""

DEFAULT_PROCESSORS_CONFIG = """batch:
  send_batch_size: 1024
  timeout: 1s
  send_batch_max_size: 2048

resource_detection:
  detectors: [env, system, docker]
  timeout: 5s

attributes:
  actions:
    - key: service.name
      action: upsert
      value: "llm-chatbot"
    - key: deployment.environment
      action: upsert
      value: "development"
    - key: service.version
      action: upsert
      value: "1.0.0"

memory_limiter:
  check_interval: 5s
  limit_mib: 512
  spike_limit_mib: 128"""

DEFAULT_EXPORTERS_CONFIG = """logging:
  loglevel: info
  sampling_initial: 2
  sampling_thereafter: 500

otlp:
  endpoint: http://jaeger:14250
  insecure: true
  sending_queue:
    queue_size: 512
  timeout: 30s

prometheus:
  endpoint: "0.0.0.0:8889"
  namespace: "llm_chatbot"
  metric_expiration: 180m
  send_metadata: true

loki:
  endpoint: http://loki:3100/loki/api/v1/push
  insecure: true
  sending_queue:
    queue_size: 512
  timeout: 30s
  labels:
    attributes: true
    resource:
      service.name: service_name
      deployment.environment: deployment_environment"""


def ensure_config_directory():
    """
    Ensure the configuration directory exists.
    """
    Path(CONFIG_DIR).mkdir(parents=True, exist_ok=True)
    logging.info(f"Ensured config directory exists: {CONFIG_DIR}")


def write_config_file(file_path: str, content: str, config_name: str):
    """
    Write configuration file with backup and validation.
    """
    try:
        # Create backup if file exists
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup"
            with open(file_path) as src, open(backup_path, "w") as dst:
                dst.write(src.read())
            logging.info(f"Created backup: {backup_path}")

        # Write new configuration
        with open(file_path, "w") as f:
            f.write(content)

        # Validate file was written correctly
        with open(file_path) as f:
            written_content = f.read()

        if written_content == content:
            logging.info(f"Successfully wrote {config_name} configuration")
            return True
        logging.error(f"Configuration validation failed for {config_name}")
        return False

    except Exception as e:
        logging.exception(f"Failed to write {config_name} configuration: {e}")
        return False


@activity.defn
async def configure_opentelemetry_collector(service_name: str) -> bool:
    """
    Configure OpenTelemetry Collector with all necessary configuration files.
    """
    logging.info(f"Configuring OpenTelemetry Collector for {service_name}")

    ensure_config_directory()

    success_count = 0

    # Write telemetry configuration
    if write_config_file(TELEMETRY_CONFIG, DEFAULT_TELEMETRY_CONFIG, "telemetry"):
        success_count += 1

    # Write receivers configuration
    if write_config_file(RECEIVERS_CONFIG, DEFAULT_RECEIVERS_CONFIG, "receivers"):
        success_count += 1

    # Write processors configuration
    if write_config_file(PROCESSORS_CONFIG, DEFAULT_PROCESSORS_CONFIG, "processors"):
        success_count += 1

    # Write exporters configuration
    if write_config_file(EXPORTERS_CONFIG, DEFAULT_EXPORTERS_CONFIG, "exporters"):
        success_count += 1

    success = success_count == 4

    if success:
        logging.info("OpenTelemetry Collector configuration completed successfully")
        # Log configuration summary
        config_files = [
            "telemetry.yaml",
            "receivers.yaml",
            "processors.yaml",
            "exporters.yaml",
        ]
        logging.info(f"Configuration files created: {', '.join(config_files)}")
    else:
        logging.error(
            f"Configuration failed: {success_count}/4 files written successfully"
        )

    return success


@activity.defn
async def validate_opentelemetry_config(service_name: str) -> dict:
    """
    Validate OpenTelemetry Collector configuration files.
    """
    logging.info(f"Validating OpenTelemetry Collector configuration for {service_name}")

    validation_results = {"valid": True, "files": {}, "errors": []}

    config_files = {
        "telemetry": TELEMETRY_CONFIG,
        "receivers": RECEIVERS_CONFIG,
        "processors": PROCESSORS_CONFIG,
        "exporters": EXPORTERS_CONFIG,
    }

    for config_name, file_path in config_files.items():
        if os.path.exists(file_path):
            try:
                with open(file_path) as f:
                    content = f.read()

                # Basic YAML validation
                import yaml

                yaml.safe_load(content)

                validation_results["files"][config_name] = {
                    "exists": True,
                    "valid": True,
                    "size": len(content),
                }
                logging.info(f"{config_name} configuration is valid")

            except yaml.YAMLError as e:
                validation_results["files"][config_name] = {
                    "exists": True,
                    "valid": False,
                    "error": str(e),
                }
                validation_results["errors"].append(f"{config_name}: {e!s}")
                validation_results["valid"] = False
                logging.exception(f"{config_name} configuration is invalid: {e}")
            except Exception as e:
                validation_results["files"][config_name] = {
                    "exists": True,
                    "valid": False,
                    "error": str(e),
                }
                validation_results["errors"].append(f"{config_name}: {e!s}")
                validation_results["valid"] = False
                logging.exception(f"Error validating {config_name} configuration: {e}")
        else:
            validation_results["files"][config_name] = {
                "exists": False,
                "valid": False,
                "error": "File not found",
            }
            validation_results["errors"].append(f"{config_name}: File not found")
            validation_results["valid"] = False
            logging.error(f"{config_name} configuration file not found")

    logging.info(
        f"Configuration validation completed: {'PASSED' if validation_results['valid'] else 'FAILED'}"
    )
    return validation_results


@activity.defn
async def update_opentelemetry_config(service_name: str, config_updates: dict) -> bool:
    """
    Update specific OpenTelemetry Collector configuration parameters.
    """
    logging.info(f"Updating OpenTelemetry Collector configuration for {service_name}")

    update_count = 0

    # Update telemetry configuration
    if "telemetry" in config_updates and os.path.exists(TELEMETRY_CONFIG):
        try:
            with open(TELEMETRY_CONFIG) as f:
                content = f.read()

            # Apply updates (simplified - could be enhanced for more complex updates)
            updated_content = content
            for key, value in config_updates["telemetry"].items():
                updated_content = updated_content.replace(f"{key}:", f"{key}: {value}")

            if write_config_file(
                TELEMETRY_CONFIG, updated_content, "telemetry (updated)"
            ):
                update_count += 1
        except Exception as e:
            logging.exception(f"Failed to update telemetry configuration: {e}")

    success = update_count > 0

    if success:
        logging.info(f"Configuration update completed: {update_count} files updated")
    else:
        logging.error("Configuration update failed")

    return success
