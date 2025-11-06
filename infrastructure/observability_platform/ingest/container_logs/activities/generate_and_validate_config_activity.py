from temporalio import activity
from ingest.container_logs.config.otel_config_builder import OtelConfigBuilder

@activity.defn
async def generate_and_validate_config_activity(template_path, log_paths, service_name, loki_endpoint):
    b = OtelConfigBuilder()
    return b.build(template_path, log_paths, service_name, loki_endpoint)

if __name__ == "__main__":
    b = OtelConfigBuilder()
    print(b.build(
        "./filelog_pipeline.yaml",
        ["/var/lib/docker/containers/x/x-json.log"],
        "demo",
        "http://localhost:3100/loki/api/v1/push"
    ))
