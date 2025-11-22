import asyncio
import logging
import sys
from pathlib import Path
from typing import Sequence, Type

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from temporalio.client import Client
from temporalio.worker import Worker
from infrastructure.orchestrator.base.base_worker import BaseWorker, WorkerConfig
from infrastructure.orchestrator.workflows.argocd_gitops_workflow import ArgoCDGitOpsWorkflow
from infrastructure.orchestrator.activities.configurations_activity.argocd_activity import (
    start_argocd_repo_server_activity,
    start_argocd_server_activity,
    stop_argocd_activity,
    delete_argocd_activity,
    argocd_login_activity,
    argocd_sync_application_activity,
    argocd_get_app_status_activity,
    argocd_create_application_activity,
    argocd_list_applications_activity,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ArgoCDWorker(BaseWorker):
    @property
    def workflows(self) -> Sequence[Type]:
        return [ArgoCDGitOpsWorkflow]

    @property
    def activities(self) -> Sequence[object]:
        return [
            start_argocd_repo_server_activity,
            start_argocd_server_activity,
            stop_argocd_activity,
            delete_argocd_activity,
            argocd_login_activity,
            argocd_sync_application_activity,
            argocd_get_app_status_activity,
            argocd_create_application_activity,
            argocd_list_applications_activity,
        ]


async def main():
    config = WorkerConfig(
        host="localhost",
        port=7233,
        queue="argocd-queue",
        namespace="default",
        max_concurrency=10,
    )
    
    worker = ArgoCDWorker(config)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())