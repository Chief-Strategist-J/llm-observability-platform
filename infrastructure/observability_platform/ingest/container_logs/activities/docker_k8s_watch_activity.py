import docker
from temporalio import activity

class ContainerWatcher:
    def __init__(self):
        self.client = docker.from_env()

    def list_containers(self):
        out = []
        for c in self.client.containers.list():
            out.append({
                "id": c.id,
                "name": c.name,
                "log_path": f"/var/lib/docker/containers/{c.id}/{c.id}-json.log"
            })
        return out

@activity.defn
async def docker_k8s_watch_activity():
    w = ContainerWatcher()
    return w.list_containers()

if __name__ == "__main__":
    w = ContainerWatcher()
    print(w.list_containers())
