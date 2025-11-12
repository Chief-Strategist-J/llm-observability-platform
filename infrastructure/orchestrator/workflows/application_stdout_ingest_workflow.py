from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow


@workflow.defn(name="ApplicationStdoutIngestWorkflow")
class ApplicationStdoutIngestWorkflow(BaseWorkflow):

    @workflow.run
    async def run(self, params: dict) -> str:
        rp = RetryPolicy(maximum_attempts=3)
        t = timedelta(minutes=5)

        conf = await workflow.execute_activity(
            "application_stdout_configure_activity",
            params,
            start_to_close_timeout=t,
            retry_policy=rp,
        )

        if not conf:
            return "configuration failed"

        await workflow.execute_activity(
            "add_loki_datasource_activity",
            params,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=rp,
        )

        await workflow.sleep(5)

        local_logs = await workflow.execute_activity(
            "discover_log_files_activity",
            conf,
            start_to_close_timeout=t,
            retry_policy=rp,
        )

        docker_logs = await workflow.execute_activity(
            "discover_docker_logs_activity",
            conf,
            start_to_close_timeout=t,
            retry_policy=rp,
        )

        discovered = sorted(set(local_logs + docker_logs))

        enriched = await workflow.execute_activity(
            "label_enrichment_activity",
            {"files": discovered, "labels": conf.get("labels", {})},
            start_to_close_timeout=t,
            retry_policy=rp,
        )

        ship_params = {
            "files": [item["path"] for item in enriched],
            "labels": enriched[0]["labels"] if enriched else conf.get("labels", {}),
            "protocol": "otlp",
            "endpoint": "http://localhost:4318",
            "batch_size": conf.get("batch_size", 100),
            "flush_interval_seconds": conf.get("flush_interval_seconds", 5),
            "timeout_seconds": 10
        }

        result = await workflow.execute_activity(
            "tail_and_ship_logs_activity",
            ship_params,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=rp,
        )

        return f"ingest started: discovered={len(discovered)} enriched={len(enriched)} status={result.get('status')}"
