import yaml
from temporalio import activity

class OtelConfigBuilder:
    def load(self, path: str):
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def dump(self, cfg) -> str:
        return yaml.safe_dump(cfg, default_flow_style=False)

    def update_filelog_paths(self, cfg, log_paths):
        cfg["receivers"]["filelog"]["include"] = log_paths
        return cfg

    def update_service_name(self, cfg, service_name):
        attrs = cfg["processors"]["resource"]["attributes"]
        for a in attrs:
            if a.get("key") == "service.name":
                a["value"] = service_name
        return cfg

    def update_loki_endpoint(self, cfg, loki_endpoint):
        cfg["exporters"]["loki"]["endpoint"] = loki_endpoint
        return cfg

    def build(self, template_path, log_paths, service_name, loki_endpoint):
        cfg = self.load(template_path)
        cfg = self.update_filelog_paths(cfg, log_paths)
        cfg = self.update_service_name(cfg, service_name)
        cfg = self.update_loki_endpoint(cfg, loki_endpoint)
        return self.dump(cfg)

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
