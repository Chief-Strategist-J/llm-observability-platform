from temporalio import activity

class LogSourceRegistry:
    def __init__(self):
        self.sources = set()

    def register(self, info):
        path = info["log_path"]
        if path not in self.sources:
            self.sources.add(path)
            return True
        return False

    def list(self):
        return list(self.sources)

registry_instance = LogSourceRegistry()

@activity.defn
async def register_log_source_activity(container_info):
    return registry_instance.register(container_info)

@activity.defn
async def list_log_sources_activity():
    return registry_instance.list()

if __name__ == "__main__":
    print(registry_instance.register({"log_path": "/var/lib/docker/containers/a/a-json.log"}))
    print(registry_instance.list())
