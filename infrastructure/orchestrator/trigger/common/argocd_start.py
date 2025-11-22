import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.orchestrator.base.base_pipeline import PipelineExecutor, WorkflowConfig


async def main():
    # Example: Deploy your LLM chat app via ArgoCD
    app_config = {
        "name": "llm-chat-app",
        "repo_url": "https://github.com/your-org/llm-chatbot-python.git",
        "path": "infrastructure/kubernetes/base/llm-chat-app",
        "dest_server": "https://kubernetes.default.svc",
        "dest_namespace": "llm-chat",
    }
    
    config = WorkflowConfig(
        service_name="argocd-gitops",
        workflow_name="ArgoCDGitOpsWorkflow",
        task_queue="argocd-queue",
        temporal_host="localhost:7233",
        web_ui_url="http://localhost:8080",
        params={
            "service_name": "argocd-gitops",
            "app_config": app_config,
        },
    )
    
    executor = PipelineExecutor(config)
    workflow_id = await executor.run_pipeline()
    
    if workflow_id:
        print(f"✓ ArgoCD deployment started: {workflow_id}")
        print(f"✓ Monitor at: http://localhost:8080")
        print(f"✓ ArgoCD UI: http://localhost:31080")
        print(f"✓ Default login: admin / admin")
    else:
        print("✗ Failed to start ArgoCD deployment")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())