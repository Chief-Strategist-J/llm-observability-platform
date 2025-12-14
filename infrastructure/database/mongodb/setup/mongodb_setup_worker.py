import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker

from infrastructure.orchestrator.activities.network.certificate_manage_activity import generate_certificates_activity
from infrastructure.orchestrator.activities.network.host_manage_activity import add_hosts_entries_activity
from infrastructure.orchestrator.activities.network.virtual_ip_manage_activity import allocate_virtual_ips_activity
from infrastructure.database.mongodb.setup.mongodb_setup_activity import setup_mongodb_activity, teardown_mongodb_activity
from infrastructure.database.mongodb.setup.mongodb_setup_workflow import MongodbSetupWorkflow

async def main():
    logging.basicConfig(level=logging.INFO)
    client = await Client.connect("localhost:7233", namespace="default")
    
    worker = Worker(
        client,
        task_queue="database-setup-queue", # Shared queue? Or separate? Shared is fine for now but limits concurrency if not scaled.
        # Actually separate workers is good practice if code differs significantly, but here is fine.
        workflows=[MongodbSetupWorkflow],
        activities=[
            allocate_virtual_ips_activity,
            generate_certificates_activity,
            add_hosts_entries_activity,
            setup_mongodb_activity,
            teardown_mongodb_activity
        ]
    )
    
    print("MongoDB Worker started on queue 'database-setup-queue'")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
