import os
import subprocess
import tempfile
from typing import Optional

class OTelCollectorAgent:
    def __init__(self, template_path: str, log_file_glob: str, service_name: str, loki_endpoint: str):
        self.template_path = template_path
        self.log_file_glob = log_file_glob
        self.service_name = service_name
        self.loki_endpoint = loki_endpoint
        self.config_path: Optional[str] = None
        self.process = None

    def build_config(self) -> str:
        with open(self.template_path, "r") as f:
            data = f.read()
        data = data.replace("${LOG_FILE_GLOB}", self.log_file_glob)
        data = data.replace("${SERVICE_NAME}", self.service_name)
        data = data.replace("${LOKI_ENDPOINT}", self.loki_endpoint)
        fd, path = tempfile.mkstemp(prefix="otel_", suffix=".yaml")
        os.write(fd, data.encode("utf-8"))
        os.close(fd)
        self.config_path = path
        return path

    def start(self):
        config = self.build_config()
        self.process = subprocess.Popen(["otelcol", "--config", config])
        return True

    def reload(self, log_file_glob: str = None, service_name: str = None, loki_endpoint: str = None):
        if log_file_glob:
            self.log_file_glob = log_file_glob
        if service_name:
            self.service_name = service_name
        if loki_endpoint:
            self.loki_endpoint = loki_endpoint
        self.build_config()
        return True

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
        return True

if __name__ == "__main__":
    agent = OTelCollectorAgent(
        template_path="./filelog_pipeline.yaml",
        log_file_glob="/var/log/*.log",
        service_name="demo-service",
        loki_endpoint="http://localhost:3100/loki/api/v1/push"
    )
    agent.start()
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        agent.stop()
