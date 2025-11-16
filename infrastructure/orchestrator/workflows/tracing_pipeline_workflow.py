from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow

@workflow.defn
class TracingPipelineWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: dict) -> str:
        if not params or not isinstance(params, dict):
            return "Error: Invalid params provided"
        
        service_name = params.get("service_name")
        if not service_name or not isinstance(service_name, str):
            return "Error: service_name is required and must be string"
        
        rp = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )
        timeout = timedelta(minutes=5)
        
        try:
            jaeger_result = await workflow.execute_activity(
                "start_jaeger_container",
                params,
                start_to_close_timeout=timeout,
                retry_policy=rp,
            )
            
            if not jaeger_result:
                return "Error: Failed to start Jaeger container"
            
            await workflow.sleep(2)
            
            grafana_result = await workflow.execute_activity(
                "start_grafana_container",
                params,
                start_to_close_timeout=timeout,
                retry_policy=rp,
            )
            
            if not grafana_result:
                return "Error: Failed to start Grafana container"
            
            return "Tracing pipeline fully configured: Jaeger + Grafana + Dashboard"
        except Exception as e:
            return f"Error: Tracing pipeline failed: {str(e)}"
