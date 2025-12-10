from __future__ import annotations

from pathlib import Path
from datetime import timedelta
from typing import Dict, Any

from temporalio import workflow
from infrastructure.observability.config.constants import OBSERVABILITY_CONFIG
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow


@workflow.defn
class LogsPipelineWorkflow(BaseWorkflow):

    async def add_required_hosts(self, trace_id: str) -> Dict[str, Any]:
        payload = {
            "trace_id": trace_id,
            "force_replace": True,
            "entries": [
                {"ip": "127.0.0.1", "hostname": "scaibu.traefik"}
            ],
        }

        result = await workflow.execute_activity(
            "add_hosts_entries_activity",
            payload,
            start_to_close_timeout=timedelta(seconds=30),
        )

        workflow.logger.info({
            "stage": "hosts_update",
            "trace_id": trace_id,
            "result": result,
        })

        return result

    async def verify_hosts(self, trace_id: str) -> Dict[str, Any]:
        payload = {
            "trace_id": trace_id,
            "hostnames": ["scaibu.traefik"],
        }

        result = await workflow.execute_activity(
            "verify_hosts_entries_activity",
            payload,
            start_to_close_timeout=timedelta(seconds=20),
        )

        workflow.logger.info({
            "stage": "hosts_verify",
            "trace_id": trace_id,
            "result": result,
        })

        return result

    async def start_traefik(self, trace_id: str) -> Any:
        result = await workflow.execute_activity(
            "start_traefik_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "stage": "start_traefik",
            "trace_id": trace_id,
            "result": result,
        })

        return result

    @workflow.run
    async def run(self, params: Dict[str, Any], config: Dict[str, Any]) -> str:
        trace_id = params.get("trace_id", "logs-pipeline")

        workflow.logger.info({
            "pipeline": "logs",
            "event": "workflow_start",
            "trace_id": trace_id
        })

        hosts_result = await self.add_required_hosts(trace_id)
        if not hosts_result.get("success"):
            workflow.logger.error({
                "pipeline": "logs",
                "stage": "hosts_add_failed",
                "trace_id": trace_id
            })
            return "logs_pipeline_failed_hosts_add"

        verify_result = await self.verify_hosts(trace_id)
        if not verify_result.get("success"):
            workflow.logger.error({
                "pipeline": "logs",
                "stage": "hosts_verify_failed",
                "trace_id": trace_id
            })
            return "logs_pipeline_failed_hosts_verify"

        await self.start_traefik(trace_id)

        workflow.logger.info({
            "pipeline": "logs",
            "event": "workflow_completed",
            "trace_id": trace_id
        })

        return "logs_pipeline_completed"
