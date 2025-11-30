import sys
from pathlib import Path
from datetime import timedelta
from typing import Dict, Any

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from temporalio import workflow
from infrastructure.observability.config.constants import OBSERVABILITY_CONFIG
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

        # Start infrastructure services
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

        # Start backend services
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
            "start_tempo_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "observability", "event": "tempo"}, "msg": "tempo_started"})

        await workflow.execute_activity(
            "start_otel_collector_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "observability", "event": "otel"}, "msg": "otel_started"})

        await workflow.sleep(10)

        dynamic_dir = params.get("dynamic_dir", "infrastructure/orchestrator/dynamicconfig")
        loki_push_url = params.get("loki_push_url", OBSERVABILITY_CONFIG.LOKI_PUSH_URL)
        loki_query_url = params.get("loki_query_url", OBSERVABILITY_CONFIG.LOKI_QUERY_URL)
        prometheus_url = params.get("prometheus_url", OBSERVABILITY_CONFIG.PROMETHEUS_URL)
        tempo_query_url = params.get("tempo_query_url", OBSERVABILITY_CONFIG.TEMPO_URL)
        grafana_url = params.get("grafana_url", OBSERVABILITY_CONFIG.GRAFANA_URL)

        # ========== LOGS PIPELINE ==========
        workflow.logger.info({
            "labels": {"pipeline": "observability", "event": "logs_pipeline_start"},
            "msg": "starting_logs_pipeline"
        })

        logs_gen_res = await workflow.execute_activity(
            "generate_config_logs",
            {"dynamic_dir": dynamic_dir, "loki_push_url": loki_push_url},
            start_to_close_timeout=timedelta(seconds=120),
        )
        logs_config_path = logs_gen_res.get("data", {}).get("config_path") if isinstance(logs_gen_res, dict) else None

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
            {"container_name": "opentelemetry-collector", "timeout_seconds": 60},
            start_to_close_timeout=timedelta(seconds=120),
        )

        await workflow.execute_activity(
            "create_grafana_datasource_activity",
            {
                "grafana_url": grafana_url,
                "grafana_user": "admin",
                "grafana_password": "SuperSecret123!",
                "datasource_name": "loki",
                "loki_url": OBSERVABILITY_CONFIG.LOKI_URL,
                "upsert_mode": "upsert",
                "org_id": 1,
            },
            start_to_close_timeout=timedelta(seconds=120),
        )

        logs_emit_res = await workflow.execute_activity(
            "emit_test_event_logs",
            {"config_path": logs_config_path},
            start_to_close_timeout=timedelta(seconds=60),
        )

        logs_token = logs_emit_res.get("data", {}).get("token") if isinstance(logs_emit_res, dict) else None

        await workflow.execute_activity(
            "verify_event_ingestion_logs",
            {
                "loki_query_url": loki_query_url,
                "logql": f'{{filename=~".+"}} |= "{logs_token}"' if logs_token else '{filename=~".+"}',
                "timeout_seconds": 60,
                "poll_interval": 2.0
            },
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "observability", "event": "logs_complete"}, "msg": "logs_pipeline_complete"})

        # ========== METRICS PIPELINE ==========
        workflow.logger.info({
            "labels": {"pipeline": "observability", "event": "metrics_pipeline_start"},
            "msg": "starting_metrics_pipeline"
        })

        metrics_gen_res = await workflow.execute_activity(
            "generate_config_metrics",
            {"dynamic_dir": dynamic_dir, "prometheus_url": prometheus_url},
            start_to_close_timeout=timedelta(seconds=120),
        )
        metrics_config_path = metrics_gen_res.get("data", {}).get("config_path") if isinstance(metrics_gen_res, dict) else None

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
            {"container_name": "opentelemetry-collector", "timeout_seconds": 60},
            start_to_close_timeout=timedelta(seconds=120),
        )

        await workflow.execute_activity(
            "create_grafana_datasource_metrics",
            {
                "grafana_url": grafana_url,
                "grafana_user": "admin",
                "grafana_password": "SuperSecret123!",
                "datasource_name": "prometheus",
                "prometheus_url": OBSERVABILITY_CONFIG.PROMETHEUS_URL,
                "upsert_mode": "upsert",
                "org_id": 1,
            },
            start_to_close_timeout=timedelta(seconds=120),
        )

        metrics_emit_res = await workflow.execute_activity(
            "emit_test_event_metrics",
            {"prometheus_url": prometheus_url},
            start_to_close_timeout=timedelta(seconds=60),
        )

        metric_data = metrics_emit_res.get("data", {}) if isinstance(metrics_emit_res, dict) else {}
        metric_name = metric_data.get("metric_name")
        metrics_token = metric_data.get("token")

        await workflow.execute_activity(
            "verify_event_ingestion_metrics",
            {
                "prometheus_query_url": f"{prometheus_url}/api/v1/query",
                "promql": f'{metric_name}{{token="{metrics_token}"}}' if metric_name and metrics_token else 'up',
                "timeout_seconds": 60,
                "poll_interval": 2.0
            },
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "observability", "event": "metrics_complete"}, "msg": "metrics_pipeline_complete"})

        # ========== TRACING PIPELINE ==========
        workflow.logger.info({
            "labels": {"pipeline": "observability", "event": "tracing_pipeline_start"},
            "msg": "starting_tracing_pipeline"
        })

        tracing_gen_res = await workflow.execute_activity(
            "generate_config_tracings",
            {"dynamic_dir": dynamic_dir, "internal_tempo_url": OBSERVABILITY_CONFIG.TEMPO_GRPC_URL},
            start_to_close_timeout=timedelta(seconds=120),
        )
        tracing_config_path = tracing_gen_res.get("data", {}).get("config_path") if isinstance(tracing_gen_res, dict) else None

        await workflow.execute_activity(
            "configure_source_paths_tracings",
            {"config_path": tracing_config_path} if tracing_config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )

        await workflow.execute_activity(
            "configure_source_tracings",
            {"config_path": tracing_config_path, "dynamic_dir": dynamic_dir} if tracing_config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )

        await workflow.execute_activity(
            "deploy_processor_tracings",
            {"dynamic_dir": dynamic_dir, "config_name": "otel-collector-tracings-generated.yaml"},
            start_to_close_timeout=timedelta(seconds=60),
        )

        await workflow.execute_activity(
            "restart_source_tracings",
            {"container_name": "opentelemetry-collector", "timeout_seconds": 60},
            start_to_close_timeout=timedelta(seconds=120),
        )

        await workflow.execute_activity(
            "create_grafana_datasource_tracings_activity",
            {
                "grafana_url": grafana_url,
                "grafana_user": "admin",
                "grafana_password": "SuperSecret123!",
                "datasource_name": "tempo",
                "tempo_url": OBSERVABILITY_CONFIG.TEMPO_URL,
                "upsert_mode": "upsert",
                "org_id": 1,
            },
            start_to_close_timeout=timedelta(seconds=120),
        )

        tracing_emit_res = await workflow.execute_activity(
            "emit_test_event_tracings",
            {
                "otlp_endpoint": "http://localhost:4317",
                "service_name": "test-tracing-service",
                "span_name": "test-span"
            },
            start_to_close_timeout=timedelta(seconds=60),
        )

        trace_id = tracing_emit_res.get("data", {}).get("token") if isinstance(tracing_emit_res, dict) else None

        await workflow.execute_activity(
            "verify_event_ingestion_tracings",
            {
                "tempo_query_url": tempo_query_url,
                "trace_id": trace_id if trace_id else "dummy-trace-id",
                "timeout_seconds": 60,
                "poll_interval": 2.0
            },
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({"labels": {"pipeline": "observability", "event": "tracing_complete"}, "msg": "tracing_pipeline_complete"})

        workflow.logger.info({"labels": {"pipeline": "observability", "event": "done"}, "msg": "workflow_complete"})

        return "observability_pipeline_completed"
