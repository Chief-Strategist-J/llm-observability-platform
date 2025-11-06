import os
import subprocess
import tempfile
from temporalio import activity

class AgentManager:
    def __init__(self):
        self.process = None
        self.config_path = None

    def push(self, config_str: str):
        fd, path = tempfile.mkstemp(prefix="otel_dynamic_", suffix=".yaml")
        with open(path, "w") as f:
            f.write(config_str)
        os.close(fd)
        self.config_path = path
        return path

    def start(self):
        if self.config_path and not self.process:
            self.process = subprocess.Popen(["otelcol", "--config", self.config_path])
        return True

    def reload(self):
        return True

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
        return True

manager_instance = AgentManager()

@activity.defn
async def push_and_reload_activity(config_str):
    manager_instance.push(config_str)
    manager_instance.reload()
    return True

@activity.defn
async def start_agent_activity():
    return manager_instance.start()

@activity.defn
async def stop_agent_activity():
    return manager_instance.stop()

if __name__ == "__main__":
    c = "receivers: {}\nprocessors: {}\nexporters: {}\nservice: {}"
    manager_instance.push(c)
    manager_instance.start()
