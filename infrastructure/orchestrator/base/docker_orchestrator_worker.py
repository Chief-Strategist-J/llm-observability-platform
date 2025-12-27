from __future__ import annotations

import asyncio
import logging
from typing import List, Any

from temporalio.client import Client
from temporalio.worker import Worker

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from infrastructure.orchestrator.base.activities import (
    check_image_exists_activity,
    pull_image_activity,
    check_container_exists_activity,
    stop_container_activity,
    remove_container_activity,
    restart_container_activity,
    verify_container_running_activity,
    inspect_container_activity,
    start_compose_activity,
    stop_compose_activity,
    get_container_logs_activity,
    check_network_exists_activity,
    delete_network_activity,
    create_network_activity,
    inspect_network_activity,
    attach_container_to_network_activity,
    verify_network_attachment_activity,
    create_tls_directories_activity,
    create_root_ca_activity,
    install_root_ca_activity,
    generate_certificate_activity,
    create_tls_configuration_activity,
    configure_traefik_activity,
    add_labels_to_compose_activity,
    health_check_activity,
    diagnostic_service_inspect_activity,
    diagnostic_container_inspect_activity,
    diagnostic_network_inspect_activity,
    diagnostic_image_inspect_activity,
    diagnostic_host_configuration_activity,
    diagnostic_listening_ports_activity,
    diagnostic_full_inspection_activity,
)
from infrastructure.orchestrator.base.workflows import (
    ServiceSetupWorkflow,
    ServiceTeardownWorkflow,
)


ACTIVITIES: List[Any] = [
    check_image_exists_activity,
    pull_image_activity,
    check_container_exists_activity,
    stop_container_activity,
    remove_container_activity,
    restart_container_activity,
    verify_container_running_activity,
    inspect_container_activity,
    start_compose_activity,
    stop_compose_activity,
    get_container_logs_activity,
    check_network_exists_activity,
    delete_network_activity,
    create_network_activity,
    inspect_network_activity,
    attach_container_to_network_activity,
    verify_network_attachment_activity,
    create_tls_directories_activity,
    create_root_ca_activity,
    install_root_ca_activity,
    generate_certificate_activity,
    create_tls_configuration_activity,
    configure_traefik_activity,
    add_labels_to_compose_activity,
    health_check_activity,
    diagnostic_service_inspect_activity,
    diagnostic_container_inspect_activity,
    diagnostic_network_inspect_activity,
    diagnostic_image_inspect_activity,
    diagnostic_host_configuration_activity,
    diagnostic_listening_ports_activity,
    diagnostic_full_inspection_activity,
]

WORKFLOWS = [
    ServiceSetupWorkflow,
    ServiceTeardownWorkflow,
]


async def run_worker(temporal_host: str = "localhost:7233", task_queue: str = "docker-orchestrator-queue") -> None:
    logger.info("event=worker_starting temporal_host=%s task_queue=%s", temporal_host, task_queue)
    client = await Client.connect(temporal_host)
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=WORKFLOWS,
        activities=ACTIVITIES,
    )
    logger.info("event=worker_started task_queue=%s workflows=%d activities=%d", task_queue, len(WORKFLOWS), len(ACTIVITIES))
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
