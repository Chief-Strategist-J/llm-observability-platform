import docker
from temporalio import activity

class ContainerMetadataDetector:
    def __init__(self):
        self.client = docker.from_env()

    def list_containers(self):
        out = []
        for c in self.client.containers.list():
            out.append({"id": c.id, "name": c.name})
        return out

    def inspect(self, container_id: str):
        return self.client.api.inspect_container(container_id)

    def detect_all_metadata(self):
        result = []
        for item in self.list_containers():
            raw = self.inspect(item["id"])
            result.append({"id": item["id"], "name": item["name"], "metadata": raw})
        return result

@activity.defn
async def detect_container_metadata_activity():
    d = ContainerMetadataDetector()
    return d.detect_all_metadata()

if __name__ == "__main__":
    d = ContainerMetadataDetector()
    print(d.detect_all_metadata())
