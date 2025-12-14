import asyncio
import logging
from temporalio.client import Client
from temporalio.worker import Worker

# Import Activities and Workflows
from infrastructure.orchestrator.activities.network.certificate_manage_activity import generate_certificates_activity
from infrastructure.orchestrator.activities.network.host_manage_activity import add_hosts_entries_activity
from infrastructure.orchestrator.activities.network.virtual_ip_manage_activity import allocate_virtual_ips_activity
from infrastructure.database.postgres.setup.postgres_setup_activity import setup_postgres_activity, teardown_postgres_activity
from infrastructure.database.postgres.setup.postgres_setup_workflow import PostgresSetupWorkflow

async def main():
    logging.basicConfig(level=logging.INFO)
    client = await Client.connect("localhost:7233", namespace="default")
    
    worker = Worker(
        client,
        task_queue="database-setup-queue",
        workflows=[PostgresSetupWorkflow],
        activities=[
            allocate_virtual_ips_activity,
            generate_certificates_activity,
            add_hosts_entries_activity,
            setup_postgres_activity,
            teardown_postgres_activity
        ]
    )
    
    print("Postgres Worker started on queue 'database-setup-queue'")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
