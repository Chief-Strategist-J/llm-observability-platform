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
from infrastructure.observability.config.observability_config import get_observability_config


@workflow.defn
class TracingPipelineWorkflow(BaseWorkflow):
    @workflow.run
    async def run(self, params: Dict[str, Any]) -> str:
        config = get_observability_config()
        
        workflow.logger.info({
            "pipeline": "tracing",
            "event": "workflow_start",
            "params_keys": list(params.keys())
        })

        traefik_result = await workflow.execute_activity(
            "start_traefik_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        
        if not traefik_result:
            workflow.logger.error({
                "pipeline": "tracing",
                "event": "traefik_start_failed",
                "port": config.traefik.external_port
            })
            raise RuntimeError(f"Traefik failed to start on port {config.traefik.external_port}")
        
        workflow.logger.info({
            "pipeline": "tracing",
            "event": "traefik_started",
            "url": config.traefik.external_url
        })

        await workflow.sleep(5)

        await workflow.execute_activity(
            "start_grafana_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "pipeline": "tracing",
            "event": "grafana_started",
            "internal_url": config.grafana.internal_url,
            "external_url": config.grafana.external_url
        })

        await workflow.execute_activity(
            "start_tempo_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "pipeline": "tracing",
            "event": "tempo_started",
            "internal_url": config.tempo.internal_url,
            "push_url": config.tempo_push_url
        })

        await workflow.execute_activity(
            "start_otel_collector_activity",
            {},
            start_to_close_timeout=timedelta(seconds=120),
        )
        workflow.logger.info({
            "pipeline": "tracing",
            "event": "otel_started",
            "container": config.otel_collector.container_name
        })

        await workflow.sleep(10)

        workflow_params = {
            **config.to_workflow_params(),
            **params
        }

        tempo_query_url = params.get("tempo_query_url", OBSERVABILITY_CONFIG.TEMPO_URL)
        grafana_url = params.get("grafana_url", OBSERVABILITY_CONFIG.GRAFANA_URL)

        workflow.logger.info({
            "pipeline": "tracing",
            "event": "endpoints_resolved",
            "tempo_query_url": tempo_query_url,
            "tempo_push_url": config.tempo_push_url,
            "grafana_url": grafana_url
        })

        gen_res = await workflow.execute_activity(
            "generate_config_tracings",
            {
                "dynamic_dir": str(config.dynamic_config_dir),
                "internal_tempo_url": OBSERVABILITY_CONFIG.TEMPO_GRPC_URL
            },
            start_to_close_timeout=timedelta(seconds=120),
        )
        
        workflow.logger.info({
            "pipeline": "tracing",
            "event": "config_generated",
            "success": gen_res.get("success") if isinstance(gen_res, dict) else False
        })

        config_path = None
        if isinstance(gen_res, dict):
            data = gen_res.get("data") or {}
            config_path = data.get("config_path")

        cfg_paths_res = await workflow.execute_activity(
            "configure_source_paths_tracings",
            {"config_path": config_path} if config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )
        
        workflow.logger.info({
            "pipeline": "tracing",
            "event": "paths_configured",
            "success": cfg_paths_res.get("success") if isinstance(cfg_paths_res, dict) else False
        })

        cfg_apply_res = await workflow.execute_activity(
            "configure_source_tracings",
            {
                "config_path": config_path,
                "dynamic_dir": str(config.dynamic_config_dir)
            } if config_path else {},
            start_to_close_timeout=timedelta(seconds=60),
        )
        
        workflow.logger.info({
            "pipeline": "tracing",
            "event": "source_configured",
            "success": cfg_apply_res.get("success") if isinstance(cfg_apply_res, dict) else False
        })

        deploy_res = await workflow.execute_activity(
            "deploy_processor_tracings",
            {
                "dynamic_dir": str(config.dynamic_config_dir),
                "config_name": Path(config_path).name if config_path else "otel-collector-tracings-generated.yaml",
            },
            start_to_close_timeout=timedelta(seconds=60),
        )
        
        workflow.logger.info({
            "pipeline": "tracing",
            "event": "processor_deployed",
            "success": deploy_res.get("success") if isinstance(deploy_res, dict) else False
        })

        restart_res = await workflow.execute_activity(
            "restart_source_tracings",
            {
                "container_name": config.otel_collector.container_name,
                "timeout_seconds": 60
            },
            start_to_close_timeout=timedelta(seconds=120),
        )
        
        workflow.logger.info({
            "pipeline": "tracing",
            "event": "source_restarted",
            "success": restart_res.get("success") if isinstance(restart_res, dict) else False
        })

        datasource_config = config.get_grafana_datasource_config("tempo")
        
        await workflow.execute_activity(
            "create_grafana_datasource_tracings_activity",
            {
                "grafana_url": config.grafana.external_url,
                "grafana_user": workflow_params.get("grafana_user", "admin"),
                "grafana_password": workflow_params.get("grafana_password", "SuperSecret123!"),
                "datasource_name": datasource_config["name"],
                "tempo_url": OBSERVABILITY_CONFIG.TEMPO_URL,  # Container-to-container URL
                "upsert_mode": "upsert",
                "org_id": 1,
            },
            start_to_close_timeout=timedelta(seconds=120),
        )
        
        workflow.logger.info({
            "pipeline": "tracing",
            "event": "grafana_datasource_created",
            "datasource": "tempo"
        })

        emit_res = await workflow.execute_activity(
            "emit_test_event_tracings",
            {
                "otlp_endpoint": config.otlp_grpc_endpoint,
                "service_name": "test-tracing-service",
                "span_name": "test-span"
            },
            start_to_close_timeout=timedelta(seconds=60),
        )
        
        workflow.logger.info({
            "pipeline": "tracing",
            "event": "test_event_emitted",
            "success": emit_res.get("success") if isinstance(emit_res, dict) else False
        })

        trace_id = None
        if isinstance(emit_res, dict):
            data = emit_res.get("data") or {}
            trace_id = data.get("token")

        workflow.logger.info({
            "pipeline": "tracing",
            "event": "trace_id_extracted",
            "trace_id": trace_id
        })

        verify_res = await workflow.execute_activity(
            "verify_event_ingestion_tracings",
            {
                "tempo_query_url": config.tempo_query_url,
                "trace_id": trace_id if trace_id else "dummy-trace-id",
                "timeout_seconds": 60,
                "poll_interval": 2.0
            },
            start_to_close_timeout=timedelta(seconds=120),
        )
        
        workflow.logger.info({
            "pipeline": "tracing",
            "event": "verification_complete",
            "success": verify_res.get("success") if isinstance(verify_res, dict) else False
        })

        workflow.logger.info({
            "pipeline": "tracing",
            "event": "workflow_complete"
        })

        return "tracing_pipeline_completed"