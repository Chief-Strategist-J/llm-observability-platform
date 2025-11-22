import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.base_pipeline import PipelineExecutor, WorkflowConfig


async def main():
    config = WorkflowConfig(
        service_name="alerting-pipeline",
        workflow_name="AlertingPipelineWorkflow",
        task_queue="alerting-pipeline-queue",
        temporal_host="localhost:7233",
        web_ui_url="http://localhost:8080",
        params={
            "service_name": "alerting-pipeline",
        },
    )
    
    executor = PipelineExecutor(config)
    workflow_id = await executor.run_pipeline()
    
    if workflow_id:
        print(f"✓ Alerting pipeline started: {workflow_id}")
        print(f"✓ Monitor at: http://localhost:8080")
        print(f"✓ Alertmanager UI: http://localhost:9093")
    else:
        print("✗ Failed to start alerting pipeline")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 