import subprocess
import tempfile

class DiscoveryService:
    def list_containers(self):
        out = subprocess.check_output(["docker", "ps", "--format", "{{.ID}} {{.Names}}"]).decode().strip()
        if not out:
            return []
        containers = []
        for line in out.split("\n"):
            cid, name = line.split(" ", 1)
            log_path = f"/var/lib/docker/containers/{cid}/{cid}-json.log"
            containers.append({"id": cid, "name": name, "log_path": log_path})
        return containers

    def detect_container_log_paths(self):
        return [x["log_path"] for x in self.list_containers()]

    def detect_container_metadata(self):
        return [{"id": x["id"], "name": x["name"]} for x in self.list_containers()]

class LogSourceRegistry:
    def __init__(self):
        self.sources = set()
    def is_new(self, path: str):
        return path not in self.sources
    def register(self, container_info):
        path = container_info["log_path"]
        if self.is_new(path):
            self.sources.add(path)
            return True
        return False

class OtelConfigBuilder:
    def build(self, log_paths):
        r = ""
        for p in log_paths:
            r += f"- {p}\n"
        return r

class AgentManager:
    def __init__(self):
        self.config_path = None
    def push(self, config_str):
        fd, path = tempfile.mkstemp(prefix="otel_dynamic_", suffix=".yaml")
        with open(path, "w") as f:
            f.write(config_str)
        self.config_path = path
        return True
    def reload(self):
        return True
