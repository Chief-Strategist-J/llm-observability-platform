from temporalio import activity
from ingest.container_logs.registry.log_source_registry import registry_instance

@activity.defn
async def register_service_activity(container_info):
    return registry_instance.register(container_info)

@activity.defn
async def list_registered_services_activity():
    return registry_instance.list()

if __name__ == "__main__":
    print(register_service_activity.__name__)
