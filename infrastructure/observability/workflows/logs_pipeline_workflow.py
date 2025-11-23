import sys
from pathlib import Path
from datetime import timedelta
from typing import Dict, Any

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from temporalio import workflow
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow

@workflow.defn
class LogsPipelineWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> str:

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "start"},
            "msg": "workflow_start"
        })

        await workflow.execute_activity(
            "start_grafana_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "grafana"},
            "msg": "grafana_started"
        })

        await workflow.execute_activity(
            "start_loki_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "loki"},
            "msg": "loki_started"
        })

        await workflow.execute_activity(
            "start_opentelemetry_collector",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "otel"},
            "msg": "otel_started"
        })

        dynamic_dir = params.get("dynamic_dir", "infrastructure/orchestrator/dynamicconfig")
        loki_push_url = params.get("loki_push_url", "http://localhost:31002/loki/api/v1/push")
        loki_query_url = params.get("loki_query_url", "http://localhost:31002/loki/api/v1/query")
        otel_container_name = params.get("otel_container_name", "opentelemetry-collector-development")

        gen_res = await workflow.execute_activity(
            "generate_config_logs",
            {"dynamic_dir": dynamic_dir, "loki_push_url": loki_push_url},
            start_to_close_timeout=timedelta(seconds=120),
        )

        config_path = None
        if isinstance(gen_res, dict):
            data = gen_res.get("data") or {}
            config_path = data.get("config_path")

        cfg_paths_res = await workflow.execute_activity(
            "configure_source_paths_logs",
            {"config_path": config_path} if config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )

        cfg_apply_res = await workflow.execute_activity(
            "configure_source_logs",
            {"config_path": config_path, "dynamic_dir": dynamic_dir} if config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )

        deploy_res = await workflow.execute_activity(
            "deploy_processor_logs",
            {
                "dynamic_dir": dynamic_dir,
                "config_name": Path(config_path).name if config_path else "otel-collector-generated.yaml",
            },
            start_to_close_timeout=timedelta(seconds=60),
        )

        restart_res = await workflow.execute_activity(
            "restart_source_logs",
            {"container_name": otel_container_name, "timeout_seconds": 60},
            start_to_close_timeout=timedelta(seconds=120),
        )

        await workflow.execute_activity(
            "create_grafana_datasource_activity",
            {
                "grafana_url": params.get("grafana_url", "http://localhost:31001"),
                "grafana_user": params.get("grafana_user", "admin"),
                "grafana_password": params.get("grafana_password", "SuperSecret123!"),
                "datasource_name": params.get("datasource_name", "loki"),
                "loki_url": params.get("loki_url", "http://localhost:31002"),
                "upsert_mode": params.get("upsert_mode", "upsert"),
                "org_id": params.get("org_id", 1),
            },
            start_to_close_timeout=timedelta(seconds=120),
        )

        emit_res = await workflow.execute_activity(
            "emit_test_event_logs",
            {"config_path": config_path},
            start_to_close_timeout=timedelta(seconds=60),
        )

        token = None
        if isinstance(emit_res, dict):
            data = emit_res.get("data") or {}
            token = data.get("token")

        logql = f'{{filename=~".+"}} |= "{token}"' if token else params.get("logql", '{filename=~".+"}')

        verify_res = await workflow.execute_activity(
            "verify_event_ingestion_logs",
            {"loki_query_url": loki_query_url, "logql": logql, "timeout_seconds": 60, "poll_interval": 2.0},
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "labels": {"pipeline": "logs", "event": "done"},
            "msg": "workflow_complete"
        })

        return "logs_pipeline_completed"