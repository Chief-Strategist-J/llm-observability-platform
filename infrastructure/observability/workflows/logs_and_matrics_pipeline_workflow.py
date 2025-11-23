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
class ObservabilityPipelineWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> str:
        workflow.logger.info({
            "labels": {"pipeline": "observability", "event": "start"},
            "msg": "workflow_start",
            "params": params
        })

        traefik_result = await workflow.execute_activity(
            "start_traefik_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        
        if not traefik_result:
            workflow.logger.error({"labels": {"pipeline": "observability", "event": "traefik"}, "msg": "traefik_failed"})
            raise RuntimeError("Traefik failed to start")
        
        workflow.logger.info({"labels": {"pipeline": "observability", "event": "traefik"}, "msg": "traefik_started"})
        await workflow.sleep(5)

        await workflow.execute_activity(
            "start_grafana_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "observability", "event": "grafana"}, "msg": "grafana_started"})

        await workflow.execute_activity(
            "start_loki_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "observability", "event": "loki"}, "msg": "loki_started"})

        await workflow.execute_activity(
            "start_prometheus_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "observability", "event": "prometheus"}, "msg": "prometheus_started"})

        await workflow.execute_activity(
            "start_opentelemetry_collector",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "observability", "event": "otel"}, "msg": "otel_started"})

        await workflow.sleep(10)

        dynamic_dir = params.get("dynamic_dir", "infrastructure/orchestrator/dynamicconfig")
        loki_push_url = params.get("loki_push_url", "http://localhost:31002/loki/api/v1/push")
        loki_query_url = params.get("loki_query_url", "http://localhost:31002/loki/api/v1/query")
        prometheus_url = params.get("prometheus_url", "http://localhost:9090")
        grafana_url = params.get("grafana_url", "http://localhost:31001")

        workflow.logger.info({
            "labels": {"pipeline": "observability", "event": "logs_pipeline_start"},
            "msg": "starting_logs_pipeline"
        })

        logs_gen_res = await workflow.execute_activity(
            "generate_config_logs",
            {"dynamic_dir": dynamic_dir, "loki_push_url": loki_push_url},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "labels": {"pipeline": "observability", "event": "logs_config"},
            "msg": "logs_config_generated",
            "result": logs_gen_res
        })

        logs_config_path = None
        if isinstance(logs_gen_res, dict):
            logs_config_path = logs_gen_res.get("data", {}).get("config_path")

        await workflow.execute_activity(
            "configure_source_paths_logs",
            {"config_path": logs_config_path} if logs_config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )

        await workflow.execute_activity(
            "configure_source_logs",
            {"config_path": logs_config_path, "dynamic_dir": dynamic_dir} if logs_config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )

        await workflow.execute_activity(
            "deploy_processor_logs",
            {"dynamic_dir": dynamic_dir, "config_name": "otel-collector-generated.yaml"},
            start_to_close_timeout=timedelta(seconds=60),
        )

        await workflow.execute_activity(
            "restart_source_logs",
            {"container_name": "opentelemetry-collector-development", "timeout_seconds": 60},
            start_to_close_timeout=timedelta(seconds=120),
        )

        await workflow.execute_activity(
            "create_grafana_datasource_activity",
            {
                "grafana_url": grafana_url,
                "grafana_user": "admin",
                "grafana_password": "SuperSecret123!",
                "datasource_name": "loki",
                "loki_url": "http://loki-development:3100",
                "upsert_mode": "upsert",
                "org_id": 1,
            },
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "observability", "event": "logs_datasource"}, "msg": "loki_datasource_created"})

        logs_emit_res = await workflow.execute_activity(
            "emit_test_event_logs",
            {"config_path": logs_config_path},
            start_to_close_timeout=timedelta(seconds=60),
        )

        logs_token = None
        if isinstance(logs_emit_res, dict):
            logs_token = logs_emit_res.get("data", {}).get("token")

        logs_verify_res = await workflow.execute_activity(
            "verify_event_ingestion_logs",
            {
                "loki_query_url": loki_query_url,
                "logql": f'{{filename=~".+"}} |= "{logs_token}"' if logs_token else '{filename=~".+"}',
                "timeout_seconds": 60,
                "poll_interval": 2.0
            },
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "labels": {"pipeline": "observability", "event": "logs_verify"},
            "msg": "logs_verification_complete",
            "result": logs_verify_res
        })

        workflow.logger.info({
            "labels": {"pipeline": "observability", "event": "metrics_pipeline_start"},
            "msg": "starting_metrics_pipeline"
        })

        metrics_gen_res = await workflow.execute_activity(
            "generate_config_metrics",
            {"dynamic_dir": dynamic_dir, "prometheus_url": prometheus_url},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "labels": {"pipeline": "observability", "event": "metrics_config"},
            "msg": "metrics_config_generated",
            "result": metrics_gen_res
        })

        metrics_config_path = None
        if isinstance(metrics_gen_res, dict):
            metrics_config_path = metrics_gen_res.get("data", {}).get("config_path")

        await workflow.execute_activity(
            "configure_source_paths_metrics",
            {"config_path": metrics_config_path} if metrics_config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )

        await workflow.execute_activity(
            "configure_source_metrics",
            {"config_path": metrics_config_path, "dynamic_dir": dynamic_dir} if metrics_config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )

        await workflow.execute_activity(
            "deploy_processor_metrics",
            {"dynamic_dir": dynamic_dir, "config_name": "otel-collector-metrics.yaml"},
            start_to_close_timeout=timedelta(seconds=60),
        )

        await workflow.execute_activity(
            "restart_source_metrics",
            {"container_name": "opentelemetry-collector-development", "timeout_seconds": 60},
            start_to_close_timeout=timedelta(seconds=120),
        )

        await workflow.execute_activity(
            "create_grafana_datasource_metrics",
            {
                "grafana_url": grafana_url,
                "grafana_user": "admin",
                "grafana_password": "SuperSecret123!",
                "datasource_name": "prometheus",
                "prometheus_url": "http://prometheus-development:9090",
                "upsert_mode": "upsert",
                "org_id": 1,
            },
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "observability", "event": "metrics_datasource"}, "msg": "prometheus_datasource_created"})

        metrics_emit_res = await workflow.execute_activity(
            "emit_test_event_metrics",
            {"prometheus_url": prometheus_url},
            start_to_close_timeout=timedelta(seconds=60),
        )

        metric_name = None
        metrics_token = None
        if isinstance(metrics_emit_res, dict):
            metric_data = metrics_emit_res.get("data", {})
            metric_name = metric_data.get("metric_name")
            metrics_token = metric_data.get("token")

        metrics_verify_res = await workflow.execute_activity(
            "verify_event_ingestion_metrics",
            {
                "prometheus_query_url": f"{prometheus_url}/api/v1/query",
                "promql": f'{metric_name}{{token="{metrics_token}"}}' if metric_name and metrics_token else 'up',
                "timeout_seconds": 60,
                "poll_interval": 2.0
            },
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "labels": {"pipeline": "observability", "event": "metrics_verify"},
            "msg": "metrics_verification_complete",
            "result": metrics_verify_res
        })

        workflow.logger.info({"labels": {"pipeline": "observability", "event": "done"}, "msg": "workflow_complete"})

        return "observability_pipeline_completed"