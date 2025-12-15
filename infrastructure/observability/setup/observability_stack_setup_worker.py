import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import asyncio
from infrastructure.orchestrator.base.base_worker import BaseWorker, WorkerConfig
from infrastructure.observability.setup.observability_stack_setup_workflow import (
    ObservabilityStackSetupWorkflow,
    ObservabilityStackTeardownWorkflow,
)

from infrastructure.observability.setup.observability_stack_setup_activities import (
    create_observability_network_activity,
    start_observability_stack_activity,
    stop_observability_stack_activity,
    verify_observability_stack_activity,
)

from infrastructure.orchestrator.activities.network.host_manage_activity import (
    add_hosts_entries_activity,
    remove_hosts_entries_activity,
    verify_hosts_entries_activity,
    restore_hosts_backup_activity,
)

from infrastructure.orchestrator.activities.network.virtual_ip_manage_activity import (
    allocate_virtual_ips_activity,
    deallocate_virtual_ips_activity,
    list_virtual_ip_allocations_activity,
    verify_virtual_ips_activity,
)

from infrastructure.orchestrator.activities.network.certificate_manage_activity import (
    generate_certificates_activity,
    delete_certificates_activity,
    verify_certificates_activity,
    list_certificates_activity,
    generate_traefik_tls_config_activity,
)

from infrastructure.orchestrator.config.docker.traefik.traefik_activity import (
    start_traefik_activity,
)


class ObservabilityStackSetupWorker(BaseWorker):

    @property
    def workflows(self):
        return [
            ObservabilityStackSetupWorkflow,
            ObservabilityStackTeardownWorkflow,
        ]

    @property
    def activities(self):
        return [
            create_observability_network_activity,
            start_observability_stack_activity,
            stop_observability_stack_activity,
            verify_observability_stack_activity,
            add_hosts_entries_activity,
            remove_hosts_entries_activity,
            verify_hosts_entries_activity,
            restore_hosts_backup_activity,
            allocate_virtual_ips_activity,
            deallocate_virtual_ips_activity,
            list_virtual_ip_allocations_activity,
            verify_virtual_ips_activity,
            generate_certificates_activity,
            delete_certificates_activity,
            verify_certificates_activity,
            list_certificates_activity,
            generate_traefik_tls_config_activity,
            start_traefik_activity,
        ]


async def main():
    cfg = WorkerConfig(
        host="localhost",
        port=7233,
        queue="observability-stack-setup-queue",
        namespace="default",
        max_concurrency=10,
    )
    worker = ObservabilityStackSetupWorker(cfg)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
