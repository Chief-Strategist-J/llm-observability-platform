import sys
import asyncio
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.base_worker import BaseWorker
from infrastructure.cicd.workflows.cicd_pipeline_workflow import CICDPipelineWorkflow
from infrastructure.cicd.activities.argocd_deploy_activity import (
    deploy_to_argocd,
    sync_argocd_application
)
from infrastructure.cicd.activities.argocd_status_activity import get_argocd_app_status


class CICDPipelineWorker(BaseWorker):
    SERVICE_NAME = "CICDPipelineWorker"
    TASK_QUEUE = "cicd-pipeline-queue"
    MAX_CONCURRENT_ACTIVITIES = 10

    def __init__(self):
        super().__init__()
        self.workflows = [CICDPipelineWorkflow]
        self.activities = [
            deploy_to_argocd,
            sync_argocd_application,
            get_argocd_app_status
        ]


async def main():
    worker = CICDPipelineWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
