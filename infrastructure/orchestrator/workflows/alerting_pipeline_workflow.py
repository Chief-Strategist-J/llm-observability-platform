from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
import logging

logger = logging.getLogger(__name__)


@workflow.defn
class AlertingPipelineWorkflow:
    @workflow.run
    async def run(self, params: dict) -> str:
        """
        Alerting Pipeline Workflow
        
        Steps:
        1. Start Alertmanager container
        2. Validate Alertmanager config
        3. Start Prometheus (if not already running)
        4. Test Slack integration
        5. Configure Prometheus to send alerts to Alertmanager
        """
        from infrastructure.orchestrator.activities.configurations_activity.alertmanager_activity import (
            start_alertmanager_activity,
            validate_alertmanager_config_activity,
            test_slack_integration_activity,
        )
        from infrastructure.orchestrator.activities.configurations_activity.prometheus_activity import (
            start_prometheus_container,
        )
        
        service_name = params.get("service_name", "alerting-pipeline")
        
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=10),
            maximum_attempts=3,
        )
        
        timeout = timedelta(minutes=5)
        
        logger.info(f"Starting Alerting Pipeline for service: {service_name}")
        
        # Step 1: Start Alertmanager
        await workflow.execute_activity(
            start_alertmanager_activity,
            params,
            start_to_close_timeout=timeout,
            retry_policy=retry_policy,
        )
        
        # Step 2: Validate config
        validation_result = await workflow.execute_activity(
            validate_alertmanager_config_activity,
            params,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )
        
        if not validation_result.get("valid"):
            return f"Error: Alertmanager config validation failed: {validation_result.get('output')}"
        
        # Step 3: Ensure Prometheus is running
        await workflow.execute_activity(
            start_prometheus_container,
            params,
            start_to_close_timeout=timeout,
            retry_policy=retry_policy,
        )
        
        # Step 4: Test Slack integration
        slack_test_result = await workflow.execute_activity(
            test_slack_integration_activity,
            params,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_policy,
        )
        
        if slack_test_result.get("success"):
            return f"Alerting pipeline fully configured for {service_name}. Slack test: OK"
        else:
            return f"Alerting pipeline configured but Slack test failed: {slack_test_result.get('output')}"