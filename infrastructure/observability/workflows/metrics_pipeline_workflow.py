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
class MetricsPipelineWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> str:
        workflow.logger.info({
            "labels": {"pipeline": "metrics", "event": "start"},
            "msg": "workflow_start",
            "params": params
        })

        dynamic_dir = params.get("dynamic_dir", "infrastructure/orchestrator/dynamicconfig")
        prometheus_url = params.get("prometheus_url", "http://localhost:9090")
        grafana_url = params.get("grafana_url", "http://localhost:31001")
        otel_container_name = params.get("otel_container_name", "opentelemetry-collector-development")

        workflow.logger.info({
            "labels": {"pipeline": "metrics", "event": "endpoints"},
            "msg": "using_endpoints",
            "prometheus_url": prometheus_url,
            "grafana_url": grafana_url
        })

        gen_res = await workflow.execute_activity(
            "generate_config_metrics",
            {"dynamic_dir": dynamic_dir, "prometheus_url": prometheus_url},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "labels": {"pipeline": "metrics", "event": "generate_config"},
            "msg": "generate_config_result",
            "result": gen_res
        })

        config_path = None
        if isinstance(gen_res, dict):
            data = gen_res.get("data") or {}
            config_path = data.get("config_path")

        cfg_paths_res = await workflow.execute_activity(
            "configure_source_paths_metrics",
            {"config_path": config_path} if config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )
        workflow.logger.info({
            "labels": {"pipeline": "metrics", "event": "configure_paths"},
            "msg": "configure_paths_result",
            "result": cfg_paths_res
        })

        cfg_apply_res = await workflow.execute_activity(
            "configure_source_metrics",
            {"config_path": config_path, "dynamic_dir": dynamic_dir} if config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )
        workflow.logger.info({
            "labels": {"pipeline": "metrics", "event": "configure_source"},
            "msg": "configure_source_result",
            "result": cfg_apply_res
        })

        deploy_res = await workflow.execute_activity(
            "deploy_processor_metrics",
            {
                "dynamic_dir": dynamic_dir,
                "config_name": Path(config_path).name if config_path else "otel-collector-metrics.yaml",
            },
            start_to_close_timeout=timedelta(seconds=60),
        )
        workflow.logger.info({
            "labels": {"pipeline": "metrics", "event": "deploy_processor"},
            "msg": "deploy_processor_result",
            "result": deploy_res
        })

        restart_res = await workflow.execute_activity(
            "restart_source_metrics",
            {"container_name": otel_container_name, "timeout_seconds": 60},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "labels": {"pipeline": "metrics", "event": "restart_source"},
            "msg": "restart_source_result",
            "result": restart_res
        })

        await workflow.execute_activity(
            "create_grafana_datasource_metrics",
            {
                "grafana_url": grafana_url,
                "grafana_user": params.get("grafana_user", "admin"),
                "grafana_password": params.get("grafana_password", "SuperSecret123!"),
                "datasource_name": params.get("datasource_name", "prometheus"),
                "prometheus_url": "http://prometheus-development:9090",
                "upsert_mode": params.get("upsert_mode", "upsert"),
                "org_id": params.get("org_id", 1),
            },
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "metrics", "event": "grafana_datasource"}, "msg": "grafana_datasource_created"})

        emit_res = await workflow.execute_activity(
            "emit_test_event_metrics",
            {"prometheus_url": prometheus_url},
            start_to_close_timeout=timedelta(seconds=60),
        )
        workflow.logger.info({
            "labels": {"pipeline": "metrics", "event": "emit_test"},
            "msg": "emit_test_result",
            "result": emit_res
        })

        token = None
        metric_name = None
        if isinstance(emit_res, dict):
            data = emit_res.get("data") or {}
            token = data.get("token")
            metric_name = data.get("metric_name")

        workflow.logger.info({
            "labels": {"pipeline": "metrics", "event": "token_extracted"},
            "msg": "synthetic_token",
            "token": token,
            "metric_name": metric_name
        })

        promql = f'{metric_name}{{token="{token}"}}' if metric_name and token else 'up'

        workflow.logger.info({
            "labels": {"pipeline": "metrics", "event": "verify_start"},
            "msg": "starting_verification",
            "promql": promql
        })

        verify_res = await workflow.execute_activity(
            "verify_event_ingestion_metrics",
            {"prometheus_query_url": f"{prometheus_url}/api/v1/query", "promql": promql, "timeout_seconds": 60, "poll_interval": 2.0},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "labels": {"pipeline": "metrics", "event": "verify_complete"},
            "msg": "verification_result",
            "result": verify_res
        })

        workflow.logger.info({"labels": {"pipeline": "metrics", "event": "done"}, "msg": "workflow_complete"})

        return "metrics_pipeline_completed"