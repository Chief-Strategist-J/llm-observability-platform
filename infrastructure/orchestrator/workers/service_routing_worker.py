import asyncio
from infrastructure.orchestrator.base.base_worker import BaseWorker, WorkerConfig
from infrastructure.orchestrator.activities.configurations_activity.service_routing_activity import (
    discover_service_hostnames_activity,
    configure_etc_hosts_activity,
)
from infrastructure.orchestrator.workflows.service_routing_setup_workflow import (
    ServiceRoutingSetupWorkflow,
)

class ServiceRoutingWorker(BaseWorker):
    @property
    def workflows(self):
        return [ServiceRoutingSetupWorkflow]

    @property
    def activities(self):
        return [
            discover_service_hostnames_activity,
            configure_etc_hosts_activity,
        ]

async def main():
    worker = ServiceRoutingWorker(
        WorkerConfig(
            host="localhost",
            queue="service-routing-queue",
            port=7233,
            namespace="default",
            max_concurrency=None,
        )
    )
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
