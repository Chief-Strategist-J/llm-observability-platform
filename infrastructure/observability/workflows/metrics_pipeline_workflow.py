import sys
from pathlib import Path
from datetime import timedelta
from typing import Dict, Any, Optional

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from temporalio import workflow
from infrastructure.observability.config.constants import OBSERVABILITY_CONFIG
from infrastructure.orchestrator.base.base_workflow import BaseWorkflow

@workflow.defn
class MetricsPipelineWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: Optional[Dict[str, Any]] = None, config: Optional[Dict[str, Any]] = None) -> str:
        params = params or {}
        config = config or {}

        workflow.logger.info({
            "pipeline": "metrics",
            "event": "workflow_start",
            "params_keys": list(params.keys())
        })

        workflow_params = {
            **(config.get("workflow_params", {}) if isinstance(config, dict) else {}),
            **params
        }

        prometheus_internal_url = (
            (config.get("prometheus") or {}).get("internal_url")
            or OBSERVABILITY_CONFIG.PROMETHEUS_URL
        )
        prometheus_query_url = config.get("prometheus_query_url") or (config.get("prometheus") or {}).get("query_url")
        grafana_external_url = (config.get("grafana") or {}).get("external_url") or OBSERVABILITY_CONFIG.GRAFANA_URL

        workflow.logger.info({
            "pipeline": "metrics",
            "event": "endpoints_resolved",
            "prometheus_url": prometheus_internal_url,
            "prometheus_query_url": prometheus_query_url,
            "grafana_url": grafana_external_url
        })

        gen_res = await workflow.execute_activity(
            "generate_config_metrics",
            {
                "dynamic_dir": str(config.get("dynamic_config_dir") or ""),
                "prometheus_url": OBSERVABILITY_CONFIG.PROMETHEUS_URL
            },
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "pipeline": "metrics",
            "event": "config_generated",
            "success": gen_res.get("success") if isinstance(gen_res, dict) else False
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
            "pipeline": "metrics",
            "event": "paths_configured",
            "success": cfg_paths_res.get("success") if isinstance(cfg_paths_res, dict) else False
        })

        cfg_apply_res = await workflow.execute_activity(
            "configure_source_metrics",
            {
                "config_path": config_path,
                "dynamic_dir": str(config.get("dynamic_config_dir") or "")
            } if config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )

        workflow.logger.info({
            "pipeline": "metrics",
            "event": "source_configured",
            "success": cfg_apply_res.get("success") if isinstance(cfg_apply_res, dict) else False
        })

        deploy_res = await workflow.execute_activity(
            "deploy_processor_metrics",
            {
                "dynamic_dir": str(config.get("dynamic_config_dir") or ""),
                "config_name": Path(config_path).name if config_path else "otel-collector-metrics.yaml",
            },
            start_to_close_timeout=timedelta(seconds=60),
        )

        workflow.logger.info({
            "pipeline": "metrics",
            "event": "processor_deployed",
            "success": deploy_res.get("success") if isinstance(deploy_res, dict) else False
        })

        restart_res = await workflow.execute_activity(
            "restart_source_metrics",
            {
                "container_name": (config.get("otel_collector") or {}).get("container_name"),
                "timeout_seconds": 60
            },
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "pipeline": "metrics",
            "event": "source_restarted",
            "success": restart_res.get("success") if isinstance(restart_res, dict) else False
        })

        datasource_config = {
            "name": "prometheus",
            "type": "prometheus",
            "url": prometheus_internal_url,
            "access": "proxy",
            "isDefault": False,
            "jsonData": {}
        }

        prometheus_url = params.get("prometheus_url") or datasource_config["url"] or OBSERVABILITY_CONFIG.PROMETHEUS_URL
        grafana_url = params.get("grafana_url") or grafana_external_url or OBSERVABILITY_CONFIG.GRAFANA_URL

        await workflow.execute_activity(
            "create_grafana_datasource_metrics",
            {
                "grafana_url": grafana_url,
                "grafana_user": workflow_params.get("grafana_user", "admin"),
                "grafana_password": workflow_params.get("grafana_password", "SuperSecret123!"),
                "datasource_name": datasource_config["name"],
                "prometheus_url": prometheus_url,
                "upsert_mode": "upsert",
                "org_id": 1,
            },
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "pipeline": "metrics",
            "event": "grafana_datasource_created",
            "datasource": "prometheus"
        })

        emit_res = await workflow.execute_activity(
            "emit_test_event_metrics",
            {"prometheus_url": prometheus_internal_url},
            start_to_close_timeout=timedelta(seconds=60),
        )

        workflow.logger.info({
            "pipeline": "metrics",
            "event": "test_event_emitted",
            "success": emit_res.get("success") if isinstance(emit_res, dict) else False
        })

        token = None
        metric_name = None
        if isinstance(emit_res, dict):
            data = emit_res.get("data") or {}
            token = data.get("token")
            metric_name = data.get("metric_name")

        workflow.logger.info({
            "pipeline": "metrics",
            "event": "token_extracted",
            "token": token,
            "metric_name": metric_name
        })

        promql = f'{metric_name}{{token="{token}"}}' if metric_name and token else 'up'

        workflow.logger.info({
            "pipeline": "metrics",
            "event": "verification_start",
            "promql": promql
        })

        verify_res = await workflow.execute_activity(
            "verify_event_ingestion_metrics",
            {
                "prometheus_query_url": prometheus_query_url,
                "promql": promql,
                "timeout_seconds": 60,
                "poll_interval": 2.0
            },
            start_to_close_timeout=timedelta(seconds=120),
        )

        workflow.logger.info({
            "pipeline": "metrics",
            "event": "verification_complete",
            "success": verify_res.get("success") if isinstance(verify_res, dict) else False
        })

        workflow.logger.info({
            "pipeline": "metrics",
            "event": "cleanup_start"
        })

        cleanup_activities = [
            "stop_prometheus_activity",
            "delete_prometheus_activity",
            "stop_otel_collector_activity",
            "delete_otel_collector_activity",
        ]

        for act in cleanup_activities:
            try:
                await workflow.execute_activity(
                    act, {}, start_to_close_timeout=timedelta(seconds=30)
                )
            except Exception:
                workflow.logger.info({
                    "pipeline": "metrics",
                    "event": "cleanup_skip",
                    "activity": act
                })

        workflow.logger.info({
            "pipeline": "metrics",
            "event": "cleanup_complete"
        })

        workflow.logger.info({
            "pipeline": "metrics",
            "event": "workflow_complete"
        })

        return "metrics_pipeline_completed"
