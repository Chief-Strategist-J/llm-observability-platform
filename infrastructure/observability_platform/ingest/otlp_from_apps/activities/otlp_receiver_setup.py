import os
import tempfile

class OTLPReceiverSetup:
    def __init__(self, template_path: str, service_name: str, otlp_endpoint: str):
        self.template_path = template_path
        self.service_name = service_name
        self.otlp_endpoint = otlp_endpoint

    def build_config(self) -> str:
        with open(self.template_path, "r") as f:
            data = f.read()
        data = data.replace("${SERVICE_NAME}", self.service_name)
        data = data.replace("${OTLP_ENDPOINT}", self.otlp_endpoint)
        return data

    def write_temp_config(self) -> str:
        cfg = self.build_config()
        fd, path = tempfile.mkstemp(prefix="otel_otlp_", suffix=".yaml")
        os.write(fd, cfg.encode("utf-8"))
        os.close(fd)
        return path

if __name__ == "__main__":
    setup = OTLPReceiverSetup(
        "./otlp_pipeline.yaml",
        "demo-service",
        "http://localhost:4317"
    )
    print(setup.build_config())
